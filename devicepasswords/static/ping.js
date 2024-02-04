const ping_api = config.api_ping
console.log("Found 'ping' endpoint: ", ping_api)

async function sleep(timeout) {
    await new Promise(r => setTimeout(r, timeout));
}


(async () => {
   for (;;) {
       await sleep(30000)
       try {
           const response = await (await fetch(ping_api)).json()
           if (!response.pong) {
               location.reload()
               break
           }
       } catch {
           // pass
       }
   }
})()