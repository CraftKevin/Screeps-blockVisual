#引入文件
# requirements:websocket-client,requests,pillow
from websocket import create_connection
import requests as req
import json
import time
import os
import random
import sys
from PIL import Image
import re

# 正则判断是否为数字
def is_number(num):
	pattern = re.compile(r'^[-+]?[-0-9]\d*\.\d*|[-+]?\.?[0-9]\d*$')
	result = pattern.match(num)
	if result:
		return True
	else:
		return False

# 命令行提示
def help(e):
	print("This tools requires these following args:")
	print("shard: The shard name of your room")
	print("roomName: The name of your room")
	print("python main.py shard roomName")
	print("eg.")
	print("python main.py shard3 E10N10")
	if type(e)==IndexError:
		print('Missing critical args')
	else:
		print(e)
	exit()

# 检查是否为标准房间名
def checkRoomName(roomName):
	if (roomName[0] != 'N' and roomName[0] != 'S' and roomName[0] != 'W' and roomName[0] != 'E')or(roomName[3] != 'N' and roomName[3] != 'S' and roomName[3] != 'W' and roomName[3] != 'E'):
		return False
	num1=is_number(roomName[1:3])
	num2=is_number(roomName[4:])
	return num1 and num2

def getRawFileList(path):
	files = []
	names = []
	for f in os.listdir(path):
		if not f.endswith("~") or not f == "":
			files.append(os.path.join(path, f))
			names.append(f)
	return files, names
	
# getTerrain(shard,roomName)
# 获取房间地形json数据
# shard:房间所在shard
# roomName:房间名称
def getTerrain(shard,roomName):
	return json.loads(req.get('https://screeps.com/api/game/room-terrain?room='+roomName+'&shard='+shard).text)

# getToken(email,password)
# 获取一个token(临时测试使用)
# email:用户邮箱
# password:用户密码
def getToken(email,password):
	try:
		return json.loads(req.post('https://screeps.com/api/auth/signin',data={'email':email,'password':password}).text)['token']
	except:
		return False
		
# setMemory(mempath,mem,token)
# 手动设置Memory
# mempath:要设置的memory路径
# mem:要设置的memory内容
# token:用户token
def setMemory(mempath,mem,token):
	try:
		path=mempath.split('/')
		cmd=''
		for d in path[:-1]:
			cmd+=' if(Memory.'+mempath[:mempath.index(d)+len(d)].replace('/','.')+'==undefined){ Memory.'+mempath[:mempath.index(d)+len(d)].replace('/','.')+'={} }'
		print(cmd+' Memory.'+mempath.replace('/','.')+'='+str(mem))
		return req.post('https://screeps.com/api/user/console',headers={'X-Token':token},data={'shard':'shard3','expression':cmd+' Memory.'+mempath.replace('/','.')+'='+str(mem)})
	except:
		return False

def render(name, background, pos, size, dir: str = os.path.join(os.path.split(os.path.abspath(__file__))[0], 'resourcepacks', 'default')):
    """pos is Obj.pos"""
    bg = background
    mddir = os.path.join(dir, 'models')
    txdir = os.path.join(dir, 'textures')
    x, y = pos
    try:
        with open(os.path.join(mddir, name + '.json')) as model_file:
            model = model_file.read()
            model = json.loads(model)
            textures = model['textures']
            faces = model['faces']
            render_rect = [-1, -1, -1, -1]
            for face in faces:
                if render_rect[0] == -1:
                    render_rect[0] = face['from'][0]
                else:
                    render_rect[0] = min(render_rect[0], face['from'][0])
                if render_rect[1] == -1:
                    render_rect[1] = face['from'][1]
                else:
                    render_rect[1] = min(render_rect[1], face['from'][1])
                if render_rect[2] == -1:
                    render_rect[2] = face['to'][0]
                else:
                    render_rect[2] = max(render_rect[2], face['to'][0])
                if render_rect[3] == -1:
                    render_rect[3] = face['to'][1]
                else:
                    render_rect[3] = max(render_rect[3], face['to'][1])
            render_rect[0] = int((render_rect[0] / 16.0 + x) * size)
            render_rect[1] = int((render_rect[1] / 16.0 + y) * size)
            render_rect[2] = int((render_rect[2] / 16.0 + x) * size)
            render_rect[3] = int((render_rect[3] / 16.0 + y) * size)
            img = Image.new('RGBA', (render_rect[2] - render_rect[0], render_rect[3] - render_rect[1]))
            raw_img = Image.open(os.path.join(txdir, textures[face['texture']])).convert('RGBA')
            w, h = img.size
            r_w, r_h = raw_img.size
            pix = img.load()
            r_pix = raw_img.load()
            for x in range(w):
                for y in range(h):
                    rx = int((face['uv'][0] * (w - x) / w + face['uv'][2] * x / w) / 16.0 * r_w)
                    ry = int((face['uv'][1] * (h - y) / h + face['uv'][3] * y / h) / 16.0 * r_h)
                    pix[x, y] = r_pix[rx, ry]
    except:
        print("Render Error:\tModel <", name, "> not found. ")
        return 0
    tmp = bg.crop(render_rect).convert('RGBA')
    tmp.alpha_composite(img)
    bg.paste(tmp, render_rect)
    return bg

if __name__=="__main__":
	rawConfig=''
	with open('config.json','r')as f:
		rawConfig=f.read()
		f.close()
	try:
		config=json.loads(rawConfig)
	except:
		sys.exit('Can\'t resolve config.json')
	token=config['token']
	# 获取传入命令行参数
	try:
		shard=sys.argv[1]
		if not('shard' in shard):
			raise RuntimeError('Wrong shard name')
		roomName=sys.argv[2]
		if len(roomName)!=6 or (not checkRoomName(roomName)):
			raise RuntimeError('Wrong room name')
	except Exception as e:
			help(e)
		
	# 命令行参数检查完成,
	ws = create_connection('wss://screeps.com/socket/133/qwerasdf/websocket')
	for i in range(4):
		print("Debug:",ws.recv()[1:])
	print('Login...')
	time.sleep(0.5)

ws.send('["auth '+token+'"]')
if ws.recv()[3:10] == 'auth ok':
    print('Token verify successfully')
else:
    print('Wrong token')
    sys.exit()

print('Loading data...')
data = ''
ws.send('"subscribe room:'+shard+'/'+roomName+'"')
data = ws.recv()
data = data[3:-2].replace('\\\\\\"', '"').replace('\\\\"',
                                                  '"').replace('\\"', '"')
try:
    if data[7:data.index(',')-1] != shard+'/'+roomName:
        data = ws.recv()
        data = data[3:-2].replace('\\\\\\"',
                                  '"').replace('\\\\"', '"').replace('\\"', '"')
except:
    pass
    # print(data)
try:
    data = data[:data.index(',"users"')]+'}'
except:
    pass
try:
    data = data[:data.index(',"visual"')]+'}'
except:
    pass
data = data[data.index(',')+1:]
if data[-1] == ']':
    data = data[:-1]
if data[-1] != '}':
    data += '}'
try:
    data = json.loads(data)
except:
    print(data)
    print('Failed')
else:
    # Render!
    res_dir = "./imgs/"
    rpname = 'default'
    pixs = 16
    bg = Image.open('./resourcepacks/' + rpname + '/textures/bg.png').convert("RGBA")
    rampart_list = []
    wall_list = {'up': [], 'down': [], 'left': [], 'right': []}
    files, names = getRawFileList(res_dir)
    roomTerrain = getTerrain(shard, roomName)
    row = []
    road = []
    for i in range(50):
        row.append(0)
    for i in range(50):
        road.append(row[:])
    if 'ok' in roomTerrain:
        if roomTerrain['ok'] == 1:
            for terrain in roomTerrain['terrain']:
                if terrain['type'] == 'wall' or terrain['type'] == 'swamp':
                    x = terrain['x']*pixs
                    y = terrain['y']*pixs
                    terrain_image = Image.open(
                        res_dir+terrain['type']+".png").convert("RGBA")
                    bg.paste(terrain_image, (x, y, x+pixs, y+pixs))
                if terrain['x'] == 0:
                    wall_list['left'].append(terrain['y'])
                if terrain['x'] == 49:
                    wall_list['right'].append(terrain['y'])
                if terrain['y'] == 0:
                    wall_list['up'].append(terrain['x'])
                if terrain['y'] == 49:
                    wall_list['down'].append(terrain['x'])

    for direction in wall_list:
        if direction == 'up':
            up = Image.open(res_dir+'up.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(up, (i*pixs, 0, i*pixs+pixs, pixs))
        if direction == 'down':
            down = Image.open(res_dir+'down.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(down, (i*pixs, 49*pixs, i*pixs+pixs, 50*pixs))
        if direction == 'left':
            left = Image.open(res_dir+'left.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(left, (0, i*pixs, pixs, i*pixs+pixs))
        if direction == 'right':
            right = Image.open(res_dir+'right.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(right, (49*pixs, i*pixs, 50*pixs, i*pixs+pixs))

    for obj in data['objects'].values():
        if 'x' not in obj:
            continue
        if 'y' not in obj:
            continue
        if 'type' not in obj:
            continue
        structure = obj['type']
        x = obj['x']*pixs
        y = obj['y']*pixs
        if structure == 'rampart':
            rampart_list.append((x, y))
            continue
        if structure == 'extension':
            tmp = bg.crop((x, y, x+pixs, y+pixs)).convert('RGBA')
            if obj['store']['energy'] < obj['storeCapacityResource']['energy']/3:
                structure_image = Image.open(
                    res_dir+structure+"_empty.png").convert("RGBA")
            else:
                structure_image = Image.open(
                    res_dir+structure+".png").convert("RGBA")
            tmp.alpha_composite(structure_image)
            bg.paste(tmp, (x, y, x+pixs, y+pixs))
            continue
        if structure == 'controller':
            bg = render('controller_' + str(obj['level']), bg, (obj['x'], obj['y']), pixs)
            continue
        if structure == 'powerSpawn' or structure == 'factory':
            bg = render(structure, bg, (obj['x'], obj['y']), pixs)
            continue

        if structure == 'road':
            road[obj['x']][obj['y']] = 1
            bg = render('road', bg, (obj['x'], obj['y']), pixs)

        elif structure == 'mineral':
            bg = render('mineral_' + obj['mineralType'], bg, (obj['x'], obj['y']), pixs)
        else:
            if structure+'.png' not in names:
                continue
            if (structure == 'tower' or structure == 'link') and obj['store']['energy'] < obj['storeCapacityResource']['energy']/3:
                structure_image = Image.open(
                    res_dir+structure+"_empty.png").convert("RGBA")
            elif structure == 'nuker' and ('energy' not in obj['store'] or 'G' not in obj['store'] or obj['store']['energy'] != 300000 or obj['store']['G'] != 5000):
                structure_image = Image.open(
                    res_dir+structure+"_empty.png").convert("RGBA")
            elif structure == 'source' and obj['energy'] == 0:
                structure_image = Image.open(
                    res_dir+structure+"_empty.png").convert("RGBA")
            else:
                structure_image = Image.open(
                    res_dir+structure+".png").convert("RGBA")
            tmp = bg.crop((x-structure_image.size[0]+pixs, y-structure_image.size[1]+pixs, x+pixs, y+pixs))
            tmp.alpha_composite(structure_image)
            bg.paste(tmp, (x-structure_image.size[0]+pixs, y-structure_image.size[1]+pixs, x+pixs, y+pixs))

    res_dir = './resourcepacks/default/textures/'

    for x in range(1,49):
        for y in range(1,49):
            if road[x][y] == 1:
                if road[x - 1][y + 1] == 1:
                    connection = Image.open(res_dir+'road_EN-WS.png').convert('RGBA')
                    x0 = x - 0.5
                    y0 = y + 0.5
                    pix_x = int(x0 * pixs)
                    pix_y = int(y0 * pixs)
                    tmp = bg.crop((pix_x, pix_y, pix_x + pixs, pix_y + pixs)).convert('RGBA')
                    tmp.alpha_composite(connection)
                    bg.paste(tmp, (pix_x, pix_y, pix_x + pixs, pix_y + pixs))
                if road[x][y + 1] == 1:
                    connection = Image.open(res_dir+'road_N-S.png').convert('RGBA')
                    x0 = x
                    y0 = y + 0.5
                    pix_x = int(x0 * pixs)
                    pix_y = int(y0 * pixs)
                    tmp = bg.crop((pix_x, pix_y, pix_x + pixs, pix_y + pixs)).convert('RGBA')
                    tmp.alpha_composite(connection)
                    bg.paste(tmp, (pix_x, pix_y, pix_x + pixs, pix_y + pixs))
                if road[x + 1][y + 1] == 1:
                    connection = Image.open(res_dir+'road_WN-ES.png').convert('RGBA')
                    x0 = x + 0.5
                    y0 = y + 0.5
                    pix_x = int(x0 * pixs)
                    pix_y = int(y0 * pixs)
                    tmp = bg.crop((pix_x, pix_y, pix_x + pixs, pix_y + pixs)).convert('RGBA')
                    tmp.alpha_composite(connection)
                    bg.paste(tmp, (pix_x, pix_y, pix_x + pixs, pix_y + pixs))
                if road[x + 1][y] == 1:
                    connection = Image.open(res_dir+'road_W-E.png').convert('RGBA')
                    x0 = x + 0.5
                    y0 = y 
                    pix_x = int(x0 * pixs)
                    pix_y = int(y0 * pixs)
                    tmp = bg.crop((pix_x, pix_y, pix_x + pixs, pix_y + pixs)).convert('RGBA')
                    tmp.alpha_composite(connection)
                    bg.paste(tmp, (pix_x, pix_y, pix_x + pixs, pix_y + pixs))

    res_dir = './imgs/'

    for pos in rampart_list:
        tmp = bg.crop((pos[0], pos[1], pos[0]+pixs,
                       pos[1]+pixs)).convert('RGBA')
        rampart = Image.open(res_dir+"rampart.png").convert("RGBA")
        tmp.alpha_composite(rampart)
        bg.paste(tmp, (pos[0], pos[1], pos[0]+pixs, pos[1]+pixs))

ws.send('"unsubscribe room:'+shard+'/'+roomName+'"')
ws.close()
bg.save('./screeps-room-'+shard+'-'+roomName+'.png')
