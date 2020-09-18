// This script registers a bot on Twitch and listens for input
// !sql SQL_COMMAND
// where SQL_COMMAND is then executed in psql.
//
// To prevent people from stomping over the host system too badly,
// a subprocess for psql is spawned and all input is explicitly
// piped to that subprocess.
//
// There are TOCTOU bugs in this file.
// Don't use for anything serious.

const fs = require('fs');                       // Append to file.
const { spawn } = require('child_process');     // Spawn subprocess.
const tmi = require('tmi.js');                  // Twitch API.

// ===== PSQL SETUP =====

// Arguments to psql. This should be pretty standard.
const psql_args = ['-h', 'localhost', '-U', 'terrier', '-p', '15721'];

var alive = false;      // Global variable, checks if psql is alive.
var psql = null;        // Global variable, the spawned psql process.
var sqlQueue = [];      // Global variable, bounded queue of sql to run.
const sqlQueueMaxLen = 20; // Bound the sqlQueue since we're using .shift().
var histBuf = [];       // Global variable, buffer of recent commands.

// Spawn psql if necessary.
function spawnPsql() {
  // If psql is already alive, do nothing.
  if (alive) return;
  console.log(`👻 psql dead or pining for the fjords, reviving.\n\n`);

  // TODO(WAN): make psql not headless, for now the startup message is faked.
  console.log('💩 # psql ' + psql_args.join(' '));
  console.log('psql (12.4 (Ubuntu 12.4-0ubuntu0.20.04.1), server 9.5devel)');
  console.log('Type "help" for help.\n');
  process.stdout.write('terrier=# ');

  // Reset the sql queue and history buffer.
  sqlQueue = [];
  histBuf = [];

  // Spawn psql. All stdout and stderr from psql will be printed.
  psql = spawn('psql', psql_args);
  psql.stdout.on('data', (data) => {
    console.log(`${data}`);
    process.stdout.write('terrier=# ');
  });
  psql.stderr.on('data', (data) => {
    console.error(`${data}`);
  });

  // If psql dies, log the exit code and mark it as dead.
  // psql will be revived by an interval task.
  psql.on('close', (code) => {
    console.log(`psql exited with code ${code}`);
    alive = false;
    fs.appendFileSync('crash.txt', histBuf.join('\n') + '\n=====\n');
  });

  // psql successfully spawned and ready for business.
  alive = true;
  sqlQueue.push(['BOT', '\\timing']);
}

// Run SQL commands if any exist.
function getAndRunSQL() {
  // If the queue is empty, there is no work to do.
  if (0 == sqlQueue.length) return;
  // Otherwise, run one SQL command.
  // TODO(WAN): terrible performance, doesn't matter if queue is <= 100 elems
  var task = sqlQueue.shift();
  var username = task[0];
  var sql = task[1];
  console.log(sql);
  histBuf.push(username + ' ' + sql);
  if (histBuf.length >= sqlQueueMaxLen) {
    histBuf.shift();
  }
  try {
    psql.stdin.write(sql + '\n');
  } catch (err) { /* heh */ }
}

// ===== TWITCH SETUP =====

// Create a twitch client.
const opts = {
  identity: {
    username: process.env.TWITCH_USERNAME,
    password: process.env.TWITCH_TOKEN,
  },
  channels: [
    process.env.TWITCH_USERNAME,
  ]
};
const client = new tmi.client(opts);

// When a message is received, if it is of the form
// !sql SQL_COMMAND
// then SQL_COMMAND is appended to sqlQueue.
function onMessageHandler (target, context, msg, self) {
  // Ignore messages sent by ourself.
  if (self) { return; }

  // Remove superfluous whitespace from the ends.
  const command = msg.trim();

  // Record !sql commands if the queue isn't full.
  if (command.startsWith('!sql ')) {
    const sql = command.substring(5);
    if (sqlQueue.length >= sqlQueueMaxLen) {
      client.say(target, `Sorry, queue too long with ${sqlQueue.length} elements, ignoring: ${sql}`);
      return;
    }
    sqlQueue.push([context.username, sql]);
    client.say(target, `Queued: ${sql}`);
  }
}

function onConnectedHandler(addr, port) {
  console.log(`Bot connected to ${addr}:${port}.`);
}

// ===== LOGIC =====

setInterval(spawnPsql, 5000);
setInterval(getAndRunSQL, 1000);
client.on('message', onMessageHandler);
client.on('connected', onConnectedHandler);
client.connect();

