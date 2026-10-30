'use strict';

// afterPack hook: fully ad-hoc re-sign the packaged app.
//
// electron-builder (with no signing identity) leaves the prebuilt
// linker-signed Electron binaries in place while rewriting Info.plist,
// which makes the bundle signature invalid. Local runs are unaffected,
// but on other machines Gatekeeper strict-validates quarantined copies
// and reports "package is damaged". Re-signing inside-out fixes that.

const { execFileSync } = require('child_process');
const path = require('path');

exports.default = async function (context) {
  const appPath = path.join(context.appOutDir, `${context.packager.appInfo.productFilename}.app`);
  console.log(`  • ad-hoc re-signing ${appPath}`);
  execFileSync('codesign', ['--force', '--deep', '--sign', '-', appPath], { stdio: 'inherit' });
  execFileSync('codesign', ['--verify', '--deep', '--strict', appPath], { stdio: 'inherit' });
};
