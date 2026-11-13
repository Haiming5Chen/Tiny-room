"""Run explicitly requested local Python in a killable worker; not a sandbox."""
import contextlib
import io
import json
import subprocess
import sys
from little_world.core.blueprint import Blueprint


def worker():
    request=json.load(sys.stdin);output=io.StringIO()
    try:
        current=Blueprint.from_json(request['current'])
        namespace={'current':current,'__name__':'__little_world_build__'}
        with contextlib.redirect_stdout(output):
            exec(compile(request['source'],'<build.py>','exec'),namespace)
        bp=namespace.get('blueprint')
        if not isinstance(bp,Blueprint):raise ValueError('Assign the finished design to blueprint (a Blueprint)')
        bp.validate()
        if len(bp.components)>3000:raise ValueError('Interactive builds support up to 3000 components')
        print(json.dumps({'blueprint':bp.to_json(),'output':output.getvalue()[-4000:]}))
    except BaseException as error:
        import traceback
        print(json.dumps({'error':''.join(traceback.format_exception(type(error),error,error.__traceback__))[-6000:]}))


def start_script(source,current):
    p=subprocess.Popen([sys.executable,'-m',__name__],stdin=subprocess.PIPE,stdout=subprocess.PIPE,stderr=subprocess.PIPE,text=True, encoding='utf-8')
    p.stdin.write(json.dumps({'source':source,'current':current.to_json()}));p.stdin.close();p.stdin=None
    return p


def decode_result(stdout,stderr=''):
    try:result=json.loads(stdout)
    except (ValueError,TypeError):raise ValueError(stderr[-2000:] or 'Python worker did not return a design')
    if 'error' in result:raise ValueError(result['error'])
    return Blueprint.from_json(result['blueprint']),result.get('output','')


def run_script(source,current,timeout=10):
    p=start_script(source,current)
    try:out,err=p.communicate(timeout=timeout)
    except subprocess.TimeoutExpired:
        p.kill();p.communicate();raise TimeoutError('Python build timed out')
    return decode_result(out,err)[0]


if __name__=='__main__':worker()
