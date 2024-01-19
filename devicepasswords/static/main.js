const token_api = config.api_tokens
console.log("Found 'token' endpoint: ", token_api)

/**
 * Create a notification that a user can dismiss.
 * @param node{Node|string}
 */
function createNotification(node) {
    const message = document.createElement("div")
    message.className = "message container"

    const content = document.createElement("div")
    content.className = "content"
    content.replaceChildren(node)

    const dismiss = document.createElement("div")
    dismiss.className = "dismiss"
    const dismissBtn = document.createElement("a")
    dismissBtn.className = "button"
    dismissBtn.onclick = (e) => {
        e.preventDefault()
        message.outerHTML = ""
    }
    dismissBtn.innerText = "×"
    dismissBtn.href = "#"
    dismiss.appendChild(dismissBtn)

    message.append(content, dismiss)
    document.getElementById("messages").appendChild(message)
}

/**
 * Return the header of the device password list.
 * @returns {HTMLTableRowElement}
 */
function header() {
    const header = document.createElement("tr");

    const name = document.createElement("th")
    name.innerText = "Token name"
    const expires = document.createElement("th")
    expires.innerText = "Expires"
    const lastUsed =  document.createElement("th")
    lastUsed.innerText = "Last used"
    const remove = document.createElement("th")
    remove.innerHTML = "<abbr title=\"Delete\">🗑</abbr>"

    header.replaceChildren(name, expires,
        config.show_last_used ? lastUsed : "", remove
    )
    return header
}

/**
 * Refresh the stored password list.
 */
async function refresh() {
    const rows = [header()]
    const passwords = await (await fetch(token_api)).json()
    if (passwords.length) {
        for (const password of passwords) {
            const row = document.createElement("tr")
            const name = document.createElement("td")
            name.innerText = password.name
            const expires = document.createElement("td")
            expires.innerText = password.expires || "never"
            const lastUsed = document.createElement("td")
            lastUsed.innerText = "never"
            const remove = document.createElement("a")
            remove.innerText = "🗑"
            remove.href = "#"
            remove.dataset["id"] = password.primary
            remove.onclick = deleteToken
            row.replaceChildren(name, expires, config.show_last_used ? lastUsed : "", remove)
            rows.push(row)
        }
    } else {
        const row = document.createElement("tr")
        row.innerHTML = "<td colspan='4'><i>No device passwords (yet).</i></td>"
        rows.push(row)
    }

    const table = document.createElement("table")
    table.replaceChildren(...rows)
    document.getElementById("passwords_container").replaceChildren(table)
}


/**
 * Delete a token, taking the "id".
 * @param e{Event}
 * @returns {Promise<void>}
 */
async function deleteToken(e) {
    e.preventDefault()
    const data = new FormData()
    data.set("id", e.currentTarget.dataset.id)

    const result = await fetch(token_api, {
        method: "DELETE",
        body: data
    })
    if (result.ok) {
        createNotification("Device password deleted.")
    } else {
        createNotification("Cannot delete password.")
    }
    const _ = refresh()
}


/**
 * Show a token.
 *
 * @param name
 * @param secret
 */
function showToken(name, secret) {
    const devicePassword = document.createElement("span")
    devicePassword.readOnly = true
    devicePassword.innerText = secret
    devicePassword.ariaLabel = "new password"
    devicePassword.className = "device-password"

    const copied = document.createElement("span")
    copied.innerText = "✓"
    copied.className = "copied"

    const button = document.createElement("a")
    button.ariaLabel = "copy"
    button.className = "copy-password"
    button.href = "#"
    button.onclick = async (e) => {
        e.preventDefault()
        await navigator.clipboard.writeText(secret)
        copied.style.visibility = "visible"
    }
    button.innerText = "🗐"

    const container = document.createElement("div")
    container.replaceChildren(
        config.no_awoo ? "" : "Awoo! ",
        "Here is your new device password. ",
        "Copy the password now, as you cannot see it later.",
        document.createElement("br"),
        button,
        devicePassword,
        copied,
        document.createElement("br"),

    )
    createNotification(container)
}


const form = document.forms.namedItem("create-password")
form.onsubmit = async (e) => {
    e.preventDefault()

    const data = new FormData()
    data.set("name", e.currentTarget.name.value)
    if (e.currentTarget.expires.checked) {
        data.set("expire", e.currentTarget.expiration.value)
    }
    data.set("state", e.currentTarget.state.value)

    e.currentTarget.reset()

    const response = await fetch(token_api, {
        method: "POST",
        body: data
    })
    if (!response.ok) {
        createNotification("Cannot create password. Try to reload the page.")
        return
    }
    const retrieved = await response.json()

    const _ = refresh()

    showToken(retrieved.name, retrieved.secret)
}
form.expires.onchange = (e) => {
    form.expiration.disabled = !e.currentTarget.checked
}

const _ = refresh()