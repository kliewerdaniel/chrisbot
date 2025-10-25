// Polyfill for self global in Node.js environment
if (typeof self === 'undefined') {
  global.self = global;
}
