import "@testing-library/jest-dom";

// Polyfill Web Encoding API for jsdom — available natively in Node 18+
// but not exposed as globals in the jsdom test environment.
import { TextDecoder, TextEncoder } from "util";
Object.assign(global, { TextDecoder, TextEncoder });
