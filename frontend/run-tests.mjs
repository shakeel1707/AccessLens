import { exec } from 'child_process';
import { promisify } from 'util';

const execAsync = promisify(exec);

(async () => {
  try {
    const { stdout, stderr } = await execAsync('npx vitest --run', {
      cwd: process.cwd(),
      maxBuffer: 10 * 1024 * 1024,
    });
    console.log('STDOUT:', stdout);
    if (stderr) console.log('STDERR:', stderr);
  } catch (error) {
    console.error('Error:', error.message);
    if (error.stdout) console.log('STDOUT:', error.stdout);
    if (error.stderr) console.log('STDERR:', error.stderr);
  }
})();
