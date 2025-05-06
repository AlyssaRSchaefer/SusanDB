// jest.setup.js
const { TextEncoder, TextDecoder } = require('util');

// Attach to the global before any tests run:
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder;
