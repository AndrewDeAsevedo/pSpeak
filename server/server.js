/**
 * This is the signal server, the peers need to know when to punch through the firewall and what IP addresses to hit so this server is
 * a temporary connection to create the p2p connection. It disconnects upon completion of data transfer.
 * 
 * 
 * 
 * 
 * 
*/
const { WebSocketServer } = require("ws");

const PORT = 8765;

// In-memory store of active rooms.
// Key: room code (string), Value: array of WebSocket connections in that room.
const rooms = {};

function generateRoomCode() {
    const phonetic_alphabet = {
        1: 'alpha',  2: 'bravo',   3: 'charlie',
        4: 'delta',  5: 'echo',    6: 'foxtrot',
        7: 'golf',   8: 'hotel',   9: 'india',
        10: 'juliett', 11: 'kilo',    12: 'lima',
        13: 'mike',   14: 'november', 15: 'oscar',
        16: 'papa',   17: 'quebec',  18: 'romeo',
        19: 'sierra', 20: 'tango',   21: 'uniform',
        22: 'victor', 23: 'whiskey', 24: 'xray',
        25: 'yankee', 26: 'zulu'
    }

    const first = getRandomIntInclusive();
    const second = getRandomIntInclusive();
    const third = getRandomIntInclusive();

    const code = phonetic_alphabet[first] + '-' + phonetic_alphabet[second]+ '-' + phonetic_alphabet[third];

    console.log(code)
    return code;
    
}

// You would think there would be a built-in library for this...
function getRandomIntInclusive() {
    const minCeiled = Math.ceil(1);
    const maxFloored = Math.floor(26);
    return Math.floor(Math.random() * (maxFloored - minCeiled + 1) + minCeiled); 
}

/**
 * Send a JSON message to a single WebSocket client.
 * We stringify the object and send it as text.
 */
function sendJSON(ws, obj) {
    // readyState 1 = OPEN. Only send if the connection is still alive.
    if (ws.readyState === 1) {
      ws.send(JSON.stringify(obj));
    }
}

function handleMessage(ws, raw){
    let msg;
    try {
        msg = JSON.parse(raw);
    } catch {
        sendJSON(ws, { event: "error", reason: "Invalid JSON" });
        return;
    }
    
    if (msg.action === "create") {
        const code = generateRoomCode();
        rooms[code] = [ws];
        ws._code = code;
        ws._data = msg.data;
        sendJSON(ws, { event: "room_created", room: code });
        console.log(`Room ${code} created. Waiting for peer...`);
        

    } else if (msg.action === "join") {
        const code = msg.room;
        const room = rooms[code];

        if (!room) {
            sendJSON(ws, { event: "error", reason: "Room not found" });
            return;
          }
          if (room.length >= 2) {
            sendJSON(ws, { event: "error", reason: "Room is full" });
            return;
        }

        room.push(ws);
        ws._code = code;
        ws._data = msg.data

        sendJSON(room[0], { event: "peer_joined" , "data" : room[1]._data});
        sendJSON(room[1], { event: "peer_joined", "data" : room[0]._data});

        console.log(`Both peers connected and data transferred. Closing their connection now.`);

        sendJSON(room[0], { event: "transferred" , "data" : "data transferred"});
        sendJSON(room[1], { event: "transferred" , "data" : "data transferred"});

        room[0].close(1000, "Transfer complete");
        room[1].close(1000, "Transfer complete");
        delete rooms[code];
    }
}


function handleDisconnect(ws) {
    const code = ws._code;
    if (!code || !rooms[code]) return;
  
    // Remove this WebSocket from the room array.
    rooms[code] = rooms[code].filter((client) => client !== ws);
  
    console.log(`Client disconnected from room ${code}`);
}   

const wss = new WebSocketServer({port: PORT});

wss.on("connection", (ws) => {
    console.log("New client connected");

    // Listen for messages from this specific client.
    ws.on("message", (raw) => handleMessage(ws, raw.toString()));

    // Listen for this client disconnecting.
    ws.on("close", () => handleDisconnect(ws));
})

console.log(`signaling server running on ws://localhost:${PORT}`);

