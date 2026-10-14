#!/usr/bin/env node
import {run} from '../../eudirective-core-work/eudirective-core/scripts/guidance-source-maintenance.mjs';
await run('sweden',process.argv[2]||'sync',process.argv[3]||null);
