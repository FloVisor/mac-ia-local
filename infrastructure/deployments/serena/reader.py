"""Read-only MCP adapter: repository explicit on every call, isolated Serena per call."""
import asyncio,json,os,pathlib,subprocess,fcntl
from contextlib import asynccontextmanager
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from mcp.server.mcpserver import MCPServer
ROOT=pathlib.Path('/repositories');STATE=pathlib.Path('/state')
CAT=json.loads(pathlib.Path('/reader/repositories.json').read_text())
LIMIT=asyncio.Semaphore(1)
mcp=MCPServer('Serena read-only repositories')
TOOLS=['find_symbol','get_symbols_overview','find_referencing_symbols','search_for_pattern']
def git(path,*args):return subprocess.check_output(['git','-c','safe.directory=*','-C',str(path),*args],text=True).strip()
def project(repository):
 group=next((k for k,v in CAT.items() if repository in v),None)
 if not group:raise ValueError('Repository outside approved allowlist')
 path=ROOT/group/repository
 if not (path/'.git').exists():raise ValueError('Repository not cloned: request explicit provisioning on docker-02')
 try:sha=git(path,'rev-parse','--verify','HEAD')
 except subprocess.CalledProcessError:raise ValueError('Empty repository: no revision to analyze')
 return path,sha
@mcp.tool()
def serena_repository_status(repository:str)->dict:
 """Check exact clone revision; remote clones do not include unpushed Mac changes."""
 path,sha=project(repository)
 return {'repository':repository,'revision':sha,'branch':git(path,'branch','--show-current'),'dirty':bool(git(path,'status','--porcelain')),'remote_has_unpushed_mac_changes':False}
@asynccontextmanager
async def analysis_lock():
 async with LIMIT:
  with (STATE/'analysis.lock').open('a') as lock:
   await asyncio.to_thread(fcntl.flock,lock.fileno(),fcntl.LOCK_EX)
   try:yield
   finally:fcntl.flock(lock.fileno(),fcntl.LOCK_UN)
async def query(repository,tool,args):
 async with analysis_lock():
  path,sha=project(repository)
  if git(path,'status','--porcelain'):raise ValueError('Dirty centralized clone: analysis refused')
  home=STATE/repository/'home';home.mkdir(parents=True,exist_ok=True)
  metadata=STATE/repository/'metadata';metadata.mkdir(parents=True,exist_ok=True)
  project_cfg=metadata/'project.yml'
  if not project_cfg.exists() and repository in ['FloVisor/mac-ia-local','FloVisor/XITHI-Infrastructure-Ops','rldet9/m3-si-mixtrio-kit']:
   languages=['typescript'] if repository.startswith('rldet9/') else ['python']
   project_cfg.write_text(json.dumps({'project_name':repository.replace('/','--'),'language_servers':languages,'read_only':True,'ignore_all_files_in_gitignore':True,'ignored_paths':['**/node_modules/**','**/.venv/**','**/__pycache__/**','ollama-v0.35.0/**','diagnostics/**','artifacts/**','toolchains/**']}))
  # Dedicated home and project metadata, outside the read-only source mount.
  cfg={'agent_interface':'tools','gui_log_window':False,'web_dashboard':False,'web_dashboard_open_on_launch':False,'base_modes':[],'default_modes':[],'fixed_tools':TOOLS,'project_serena_folder_location':str(STATE/repository/'metadata'),'trusted_project_path_patterns':[],'projects':[]}
  (home/'serena_config.yml').write_text(json.dumps(cfg))
  context=STATE/'readonly-context.yml'
  env=dict(os.environ,SERENA_HOME=str(home),UV_CACHE_DIR='/state/runtime/uv-cache',UV_PYTHON_INSTALL_DIR='/state/runtime/python')
  params=StdioServerParameters(command='serena',args=['start-mcp-server','--project',str(path),'--context',str(context),'--agent-interface','tools','--enable-web-dashboard','false'],env=env)
  with (STATE/repository/'stderr.log').open('a') as err:
   async with asyncio.timeout(240):
    async with stdio_client(params,errlog=err) as (r,w):
     async with ClientSession(r,w) as session:
      await session.initialize()
      available={t.name for t in (await session.list_tools()).tools}
      if not available<=set(TOOLS):raise RuntimeError('Unexpected Serena tools: refusing analysis')
      result=await session.call_tool(tool,args)
      if result.is_error:raise RuntimeError(result.model_dump_json())
  after=git(path,'rev-parse','HEAD')
  if after!=sha or git(path,'status','--porcelain'):raise RuntimeError('Revision changed during analysis: discard result')
  (STATE/repository/'last-analysis.json').write_text(json.dumps({'repository':repository,'revision':sha,'tool':tool}))
  return {'repository':repository,'revision':sha,'tool':tool,'result':result.model_dump(mode='json',by_alias=True),'remote_has_unpushed_mac_changes':False}
@mcp.tool()
async def serena_find_symbol(repository:str,name_path_pattern:str,relative_path:str='',include_body:bool=False,depth:int=0)->dict:
 """Find real functions/classes/methods semantically using Serena LSP; repository is explicit."""
 return await query(repository,'find_symbol',dict(name_path_pattern=name_path_pattern,relative_path=relative_path,include_body=include_body,depth=depth,max_answer_chars=20000))
@mcp.tool()
async def serena_symbols_overview(repository:str,relative_path:str,depth:int=0)->dict:
 """List real symbols in a source file with Serena LSP."""
 return await query(repository,'get_symbols_overview',dict(relative_path=relative_path,depth=depth,max_answer_chars=20000))
@mcp.tool()
async def serena_find_references(repository:str,name_path:str,relative_path:str)->dict:
 """Find semantic references to a function/class/method with Serena LSP."""
 return await query(repository,'find_referencing_symbols',dict(name_path=name_path,relative_path=relative_path,max_answer_chars=20000))
@mcp.tool()
async def serena_search_pattern(repository:str,substring_pattern:str,relative_path:str='')->dict:
 """Search a code pattern using Serena; this is textual search, not semantic symbol resolution."""
 return await query(repository,'search_for_pattern',dict(substring_pattern=substring_pattern,relative_path=relative_path,max_answer_chars=20000))
if __name__=='__main__':
 STATE.mkdir(parents=True,exist_ok=True)
 (STATE/'readonly-context.yml').write_text(json.dumps({'description':'Read-only immutable single-project analysis','prompt':'Analyze source only. Never edit code.','single_project':True,'fixed_tools':TOOLS}))
 mcp.run(transport='stdio')
