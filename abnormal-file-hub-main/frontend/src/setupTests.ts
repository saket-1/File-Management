// src/setupTests.ts
import { TextEncoder, TextDecoder } from 'util';
global.TextEncoder = TextEncoder;
global.TextDecoder = TextDecoder as any; // Cast as any to match potential global type discrepancies

// This file is automatically executed by react-scripts before running tests.

// Import jest-dom matchers like expect(element).toBeInTheDocument()
import '@testing-library/jest-dom'; 