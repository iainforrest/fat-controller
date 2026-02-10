#!/usr/bin/env node

const fs = require('fs');
const path = require('path');
const readline = require('readline');

// ANSI color codes for better UX
const colors = {
  reset: '\x1b[0m',
  bright: '\x1b[1m',
  cyan: '\x1b[36m',
  green: '\x1b[32m',
  yellow: '\x1b[33m',
  blue: '\x1b[34m',
  magenta: '\x1b[35m'
};

function log(message, color = 'reset') {
  console.log(`${colors[color]}${message}${colors.reset}`);
}

function header() {
  console.log('\n');
  log('┌─────────────────────────────────────────────────────────┐', 'cyan');
  log('│                                                         │', 'cyan');
  log('│         Claude Project Starter v3.1 Installer           │', 'cyan');
  log('│                                                         │', 'cyan');
  log('│    AI-assisted development workflow for any project     │', 'cyan');
  log('│                                                         │', 'cyan');
  log('└─────────────────────────────────────────────────────────┘', 'cyan');
  console.log('\n');
}

function createInterface() {
  return readline.createInterface({
    input: process.stdin,
    output: process.stdout
  });
}

function question(rl, query) {
  return new Promise(resolve => rl.question(query, resolve));
}

function copyRecursive(src, dest) {
  const stats = fs.statSync(src);

  if (stats.isDirectory()) {
    if (!fs.existsSync(dest)) {
      fs.mkdirSync(dest, { recursive: true });
    }

    const files = fs.readdirSync(src);
    files.forEach(file => {
      copyRecursive(path.join(src, file), path.join(dest, file));
    });
  } else {
    fs.copyFileSync(src, dest);
  }
}

function checkExistingInstallation(targetDir) {
  const claudeDir = path.join(targetDir, '.claude');
  const aiDir = path.join(targetDir, '.ai');

  return {
    hasClaudeDir: fs.existsSync(claudeDir),
    hasAiDir: fs.existsSync(aiDir)
  };
}

async function promptForSetupType(rl) {
  log('\nChoose your setup type:', 'bright');
  log('  1. New Project     - Start fresh, will ask questions to populate .ai/', 'blue');
  log('  2. Existing Project - Explore your codebase and extract knowledge', 'blue');
  console.log();

  let answer = await question(rl, colors.green + 'Enter your choice (1 or 2): ' + colors.reset);
  answer = answer.trim();

  while (answer !== '1' && answer !== '2') {
    log('Invalid choice. Please enter 1 or 2.', 'yellow');
    answer = await question(rl, colors.green + 'Enter your choice (1 or 2): ' + colors.reset);
    answer = answer.trim();
  }

  return answer === '1' ? 'new' : 'existing';
}

async function promptForOverwrite(rl, existing) {
  if (existing.hasClaudeDir || existing.hasAiDir) {
    log('\nExisting installation detected:', 'yellow');
    if (existing.hasClaudeDir) log('  - .claude/ directory found', 'yellow');
    if (existing.hasAiDir) log('  - .ai/ directory found', 'yellow');
    console.log();

    const answer = await question(rl, colors.yellow + 'Overwrite existing installation? (y/N): ' + colors.reset);
    return answer.trim().toLowerCase() === 'y';
  }
  return true;
}

async function installFiles(setupType) {
  const targetDir = process.cwd();
  const sourceDir = __dirname;

  log('\nInstalling Claude Project Starter files...', 'bright');

  // Copy .claude directory
  const claudeSrc = path.join(sourceDir, '.claude');
  const claudeDest = path.join(targetDir, '.claude');
  log('  Copying .claude/ (commands and agents)...', 'blue');
  copyRecursive(claudeSrc, claudeDest);

  // Copy .ai directory from templates (not active memory)
  const aiSrc = path.join(sourceDir, 'templates', '.ai');
  const aiDest = path.join(targetDir, '.ai');
  log('  Copying .ai/ (memory system templates)...', 'blue');
  copyRecursive(aiSrc, aiDest);

  // Copy installer guides
  const newInstallSrc = path.join(sourceDir, 'INSTALL-NEW.md');
  const newInstallDest = path.join(targetDir, 'INSTALL-NEW.md');
  log('  Copying INSTALL-NEW.md...', 'blue');
  fs.copyFileSync(newInstallSrc, newInstallDest);

  const existingInstallSrc = path.join(sourceDir, 'INSTALL-EXISTING.md');
  const existingInstallDest = path.join(targetDir, 'INSTALL-EXISTING.md');
  log('  Copying INSTALL-EXISTING.md...', 'blue');
  fs.copyFileSync(existingInstallSrc, existingInstallDest);

  // Create tasks directory if it doesn't exist
  const tasksDir = path.join(targetDir, 'tasks');
  if (!fs.existsSync(tasksDir)) {
    fs.mkdirSync(tasksDir);
    log('  Created tasks/ directory...', 'blue');
  }

  log('\n✓ Files installed successfully!', 'green');

  return setupType;
}

function printNextSteps(setupType) {
  log('\n┌─────────────────────────────────────────────────────────┐', 'cyan');
  log('│                     Next Steps                          │', 'cyan');
  log('└─────────────────────────────────────────────────────────┘', 'cyan');
  console.log();

  if (setupType === 'new') {
    log('1. Open Claude Code in this directory', 'blue');
    log('2. Run the installer:', 'blue');
    log('   @INSTALL-NEW.md', 'green');
    log('\n   This will ask you questions about your project and', 'magenta');
    log('   populate the .ai/ memory system with your answers.', 'magenta');
  } else {
    log('1. Open Claude Code in this directory', 'blue');
    log('2. Run the installer:', 'blue');
    log('   @INSTALL-EXISTING.md', 'green');
    log('\n   This will explore your codebase and extract knowledge', 'magenta');
    log('   into the .ai/ memory system automatically.', 'magenta');
  }

  console.log();
  log('3. Start building with the workflow:', 'blue');
  log('   /prd → /TaskGen → /execute → /commit → /update', 'green');
  console.log();

  log('For help and documentation:', 'yellow');
  log('  https://github.com/iainforrest/fat-controller', 'yellow');
  console.log('\n');
}

async function main() {
  header();

  const targetDir = process.cwd();
  const sourceDir = __dirname;

  // Check if running from npm/npx or from source
  const isNpmInstall = !fs.existsSync(path.join(sourceDir, '.git'));

  if (!isNpmInstall && targetDir === sourceDir) {
    log('Error: Please run this from your project directory, not from the source.', 'yellow');
    log('Usage: npx create-claude-project', 'green');
    process.exit(1);
  }

  const rl = createInterface();

  try {
    // Check for existing installation
    const existing = checkExistingInstallation(targetDir);

    // Prompt for overwrite if necessary
    const shouldProceed = await promptForOverwrite(rl, existing);
    if (!shouldProceed) {
      log('\nInstallation cancelled.', 'yellow');
      rl.close();
      process.exit(0);
    }

    // Prompt for setup type
    const setupType = await promptForSetupType(rl);

    // Install files
    await installFiles(setupType);

    // Print next steps
    printNextSteps(setupType);

  } catch (error) {
    log('\nError during installation:', 'yellow');
    log(error.message, 'yellow');
    process.exit(1);
  } finally {
    rl.close();
  }
}

// Run if called directly
if (require.main === module) {
  main();
}

module.exports = { main };
