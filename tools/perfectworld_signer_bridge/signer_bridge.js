"use strict";

const fs = require("fs");
const path = require("path");

function fail(message, code = 1) {
  process.stdout.write(JSON.stringify({ error: message }));
  process.exit(code);
}

function readInput() {
  try {
    return JSON.parse(fs.readFileSync(0, "utf8"));
  } catch {
    fail("invalid JSON input");
  }
}

function validatePayload(payload) {
  for (const key of ["randnum", "ts", "data"]) {
    if (typeof payload[key] !== "string" || payload[key].length === 0) {
      fail(`missing ${key}`);
    }
  }
  if (payload.data.length > 8192) {
    fail("data is too large");
  }
  return {
    randnum: payload.randnum,
    ts: payload.ts,
    data: payload.data,
    version: Number.isInteger(payload.version) ? payload.version : 1,
  };
}

function gameAddonPath() {
  const directPath = process.env.PERFECTWORLD_GAMEADDON_NODE;
  if (directPath) {
    return directPath;
  }
  const clientDir = process.env.PERFECTWORLD_CLIENT_DIR;
  if (clientDir) {
    return path.join(clientDir, "plugin", "gameaddon.node");
  }
  fail("PERFECTWORLD_GAMEADDON_NODE or PERFECTWORLD_CLIENT_DIR is required");
}

function pluginDir() {
  const directPath = process.env.PERFECTWORLD_PLUGIN_DIR;
  if (directPath) {
    return directPath;
  }
  const clientDir = process.env.PERFECTWORLD_CLIENT_DIR;
  if (clientDir) {
    return path.join(clientDir, "plugin");
  }
  return path.dirname(path.resolve(gameAddonPath()));
}

function loadGameAddon(modulePath) {
  const resolved = path.resolve(modulePath);
  if (!fs.existsSync(resolved)) {
    fail("gameaddon.node was not found");
  }
  process.chdir(path.dirname(resolved));
  try {
    return require(resolved);
  } catch (error) {
    fail(`failed to load gameaddon.node: ${error.message}`);
  }
}

function extractSignature(value) {
  if (typeof value === "string") {
    const trimmed = value.trim();
    if (!trimmed.startsWith("{")) {
      return trimmed;
    }
    try {
      const parsed = JSON.parse(trimmed);
      return extractSignature(parsed);
    } catch {
      return trimmed;
    }
  }
  if (value && typeof value === "object") {
    for (const key of ["signature", "sign", "s", "data"]) {
      if (typeof value[key] === "string" && value[key]) {
        return value[key];
      }
    }
  }
  return "";
}

const payload = validatePayload(readInput());
const gameAddon = loadGameAddon(gameAddonPath());
const init = gameAddon.init || gameAddon.default?.init;
if (typeof init === "function") {
  try {
    init(JSON.stringify({ pluginDir: path.resolve(pluginDir()) }));
  } catch (error) {
    fail(`gameaddon init failed: ${error.message}`);
  }
}
const startCallbackService = gameAddon.StartCallbackService || gameAddon.default?.StartCallbackService;
if (typeof startCallbackService === "function") {
  try {
    startCallbackService(() => {});
  } catch (error) {
    fail(`StartCallbackService failed: ${error.message}`);
  }
}
const sendJsonMessage = gameAddon.sendJsonMessage || gameAddon.default?.sendJsonMessage;
if (typeof sendJsonMessage !== "function") {
  fail("gameaddon.node does not expose sendJsonMessage");
}

const loginId = process.env.PERFECTWORLD_LOGIN_ID || process.env.PERFECTWORLD_LOGIN_STEAM64 || "";
if (loginId) {
  try {
    sendJsonMessage(JSON.stringify({ msg_id: "LOGIN_STATUS", login: true, id: loginId }));
  } catch (error) {
    fail(`LOGIN_STATUS failed: ${error.message}`);
  }
}

const message = {
  msg_id: "SWAP_DATA",
  data: JSON.stringify({
    randnum: payload.randnum,
    ts: payload.ts,
    data: payload.data,
    version: payload.version,
  }),
};

let result;
try {
  result = sendJsonMessage(JSON.stringify(message));
} catch (error) {
  fail(`SWAP_DATA failed: ${error.message}`);
}

const signature = extractSignature(result);
if (!signature) {
  fail("SWAP_DATA returned an empty signature");
}

process.stdout.write(JSON.stringify({ signature }));
