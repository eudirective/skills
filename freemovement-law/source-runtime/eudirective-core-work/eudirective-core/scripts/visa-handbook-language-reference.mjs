#!/usr/bin/env node
// Compatibility entry point for the official Commission-register retrieval lane.
import {run} from './visa-handbook-register.mjs';
await run(process.argv[2]||'sync');
