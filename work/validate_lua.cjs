const fs = require('fs');
const path = require('path');
const crypto = require('crypto');
const root = path.resolve(__dirname, '..');
const parser = require(path.join(root, 'tools/lua-validation/node_modules/luaparse'));
const dir = path.resolve(root, process.argv[2] || 'outputs/reconstruction');
const files = [];
function visit(directory) {
  for (const entry of fs.readdirSync(directory, {withFileTypes:true})) {
    const p = path.join(directory, entry.name);
    if (entry.isDirectory()) visit(p);
    else if (entry.name.endsWith('.lua')) files.push(p);
  }
}
visit(dir);
const results = files.map(file => {
  const bytes = fs.readFileSync(file);
  parser.parse(bytes.toString('utf8'), {luaVersion:'5.1', encodingMode:'pseudo-latin1'});
  return {file:path.relative(dir,file), sha256:crypto.createHash('sha256').update(bytes).digest('hex'), syntax:'passed'};
});
const report = {tool:'luaparse', version:parser.version, lua_version:'5.1',
  execution_host:process.env.COMPUTERNAME, scope:'Syntax only; no Lua or game execution',
  files_checked:results.length, results};
fs.writeFileSync(path.join(dir,'syntax-validation.json'),JSON.stringify(report,null,2));
console.log(JSON.stringify({tool:report.tool,version:report.version,files_checked:results.length,passed:true}));
