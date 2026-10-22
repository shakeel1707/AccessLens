#!/usr/bin/env node
/**
 * Script to verify vitest configuration is correct
 */

const fs = require('fs');
const path = require('path');

console.log('🔍 Verifying Vitest Configuration...\n');

const checks = [];

// Check 1: vitest.config.ts exists
const vitestConfigPath = path.join(__dirname, 'vitest.config.ts');
checks.push({
  name: 'vitest.config.ts exists',
  passed: fs.existsSync(vitestConfigPath),
});

// Check 2: vite.config.ts exists
const viteConfigPath = path.join(__dirname, 'vite.config.ts');
checks.push({
  name: 'vite.config.ts exists',
  passed: fs.existsSync(viteConfigPath),
});

// Check 3: tsconfig.json exists and includes tests
const tsconfigPath = path.join(__dirname, 'tsconfig.json');
let tsconfigHasTests = false;
if (fs.existsSync(tsconfigPath)) {
  const tsconfig = JSON.parse(fs.readFileSync(tsconfigPath, 'utf-8'));
  tsconfigHasTests = tsconfig.include && tsconfig.include.includes('tests');
}
checks.push({
  name: 'tsconfig.json includes "tests"',
  passed: tsconfigHasTests,
});

// Check 4: Test files exist
const testDir = path.join(__dirname, 'tests');
const testFiles = fs.readdirSync(testDir).filter(f => f.endsWith('.test.ts') || f.endsWith('.test.tsx'));
checks.push({
  name: `Test files found (${testFiles.length})`,
  passed: testFiles.length > 0,
});

// Check 5: Package.json has vitest
const pkgPath = path.join(__dirname, 'package.json');
let hasVitest = false;
if (fs.existsSync(pkgPath)) {
  const pkg = JSON.parse(fs.readFileSync(pkgPath, 'utf-8'));
  hasVitest = (pkg.devDependencies && pkg.devDependencies.vitest) || 
               (pkg.dependencies && pkg.dependencies.vitest);
}
checks.push({
  name: 'vitest in package.json',
  passed: hasVitest,
});

// Print results
console.log('Configuration Checks:');
console.log('─'.repeat(50));
checks.forEach(check => {
  const icon = check.passed ? '✅' : '❌';
  console.log(`${icon} ${check.name}`);
});

console.log('─'.repeat(50));

const allPassed = checks.every(c => c.passed);
console.log(`\nResult: ${allPassed ? '✅ All checks passed!' : '❌ Some checks failed'}\n`);

if (allPassed) {
  console.log('📝 Configuration looks good. Run: npm test -- --run\n');
}

process.exit(allPassed ? 0 : 1);
