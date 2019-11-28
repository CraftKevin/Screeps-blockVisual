#
from websocket import create_connection
import requests as req
import json
import time
import os
import random
import sys
from PIL import Image
#


def getRawFileList(path):
    files = []
    names = []
    for f in os.listdir(path):
        if not f.endswith("~") or not f == "":
            files.append(os.path.join(path, f))
            names.append(f)
    return files, names

def getTerrain(shard,roomName):
    return json.loads(req.get('https://screeps.com/api/game/room-terrain?room='+roomName+'&shard='+shard).text)
def getToken(email,password):
    try:
        return json.loads(req.post('https://screeps.com/api/auth/signin',data={'email':email,'password':password}).text)['token']
    except:
        return False

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

shard=sys.argv[1]
roomName=sys.argv[2]

ws = create_connection('wss://screeps.com/socket/133/qwerasdf/websocket')

for i in range(4):
    print(ws.recv()[1:])

print('Login...')
time.sleep(0.5)

#Default Token
token='[Your-Token]'
#getToken()


ws.send('["auth '+token+'"]')
if ws.recv()[3:10]=='auth ok':
    print('Token verify successfully')
else:
    print('Wrong token')
    sys.exit()

print('Loading data...')
data=''
ws.send('"subscribe room:'+shard+'/'+roomName+'"')
data=ws.recv()
data=data[3:-2].replace('\\\\\\"','"').replace('\\\\"','"').replace('\\"','"')
try:
    if data[7:data.index(',')-1]!=shard+'/'+roomName:
        data=ws.recv()
        data=data[3:-2].replace('\\\\\\"','"').replace('\\\\"','"').replace('\\"','"')
except:
    pass
    #print(data)
try:
    data=data[:data.index(',"users"')]+'}'
except:
    pass
try:
    data=data[:data.index(',"visual"')]+'}'
except:
    pass
data=data[data.index(',')+1:]
if data[-1]==']':
    data=data[:-1]
if data[-1]!='}':
    data+='}'
try:
    data=json.loads(data)
except:
    print(data)
    print('Failed')
else:
    #print(data)
    res_dir = "./img/"
    bg = Image.open(res_dir+'bg.png').convert("RGBA")
    rampart_list=[]
    wall_list={'up':[],'down':[],'left':[],'right':[]}
    files,names=getRawFileList(res_dir)
    roomTerrain=getTerrain(shard,roomName)
    if 'ok' in roomTerrain:
        if roomTerrain['ok']==1:
            for terrain in roomTerrain['terrain']:
                if terrain['type']=='wall' or terrain['type']=='swamp':
                    x=terrain['x']*16
                    y=terrain['y']*16
                    terrain_image=Image.open(res_dir+terrain['type']+".png").convert("RGBA")
                    bg.paste(terrain_image,(x,y,x+16,y+16))
                if terrain['x']==0:
                    wall_list['left'].append(terrain['y'])
                if terrain['x']==49:
                    wall_list['right'].append(terrain['y'])
                if terrain['y']==0:
                    wall_list['up'].append(terrain['x'])
                if terrain['y']==49:
                    wall_list['down'].append(terrain['x'])

    for direction in wall_list:
        if direction=='up':
            up=Image.open(res_dir+'up.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(up,(i*16,0,i*16+16,16))
        if direction=='down':
            down=Image.open(res_dir+'down.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(down,(i*16,49*16,i*16+16,50*16))
        if direction=='left':
            left=Image.open(res_dir+'left.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(left,(0,i*16,16,i*16+16))
        if direction=='right':
            right=Image.open(res_dir+'right.png').convert('RGBA')
            for i in range(49):
                if i not in wall_list[direction]:
                    bg.paste(right,(49*16,i*16,50*16,i*16+16))
                
    
    for obj in data['objects'].values():
        if 'x' not in obj:
            continue
        if 'y' not in obj:
            continue
        if 'type' not in obj:
            continue
        structure=obj['type']
        x=obj['x']*16
        y=obj['y']*16
        if structure=='rampart':
            rampart_list.append((x,y))
            continue
        if structure=='extension':
            tmp = bg.crop((x,y,x+16,y+16)).convert('RGBA')
            if obj['store']['energy']<obj['storeCapacityResource']['energy']/3:
                structure_image=Image.open(res_dir+structure+"_empty.png").convert("RGBA")
            else:
                structure_image=Image.open(res_dir+structure+".png").convert("RGBA")
            tmp.alpha_composite(structure_image)
            bg.paste(tmp,(x,y,x+16,y+16))
            continue
        if structure=='powerSpawn' or structure=='factory':
            size=16
            real_size=22
            frame_size=real_size-size
            tmp = bg.crop((x-frame_size//2,y-frame_size//2,x+16+frame_size//2,y+16+frame_size//2)).convert('RGBA')
            structure_image=Image.open(res_dir+structure+".png").convert("RGBA")
            tmp.alpha_composite(structure_image)
            bg.paste(tmp,(x-frame_size//2,y-frame_size//2,x+16+frame_size//2,y+16+frame_size//2))
            continue
        if structure=='mineral':
            structure_image=Image.open(res_dir+obj['mineralType']+".png").convert("RGBA")
        else:
            if structure+'.png' not in names:
                continue
            if (structure=='tower' or structure=='link') and obj['store']['energy']<obj['storeCapacityResource']['energy']/3:
                structure_image=Image.open(res_dir+structure+"_empty.png").convert("RGBA")
            elif structure=='nuker' and (obj['store']['energy']<270000 or obj['store']['G']<4500):
                structure_image=Image.open(res_dir+structure+"_empty.png").convert("RGBA")
            elif structure=='source' and obj['energy']==0:
                structure_image=Image.open(res_dir+structure+"_empty.png").convert("RGBA")
            else:
                structure_image=Image.open(res_dir+structure+".png").convert("RGBA")
        bg.paste(structure_image,(x-structure_image.size[0]+16,y-structure_image.size[1]+16,x+16,y+16))

    for pos in rampart_list:
        tmp = bg.crop((pos[0],pos[1],pos[0]+16,pos[1]+16)).convert('RGBA')
        rampart=Image.open(res_dir+"rampart.png").convert("RGBA")
        tmp.alpha_composite(rampart)
        bg.paste(tmp,(pos[0],pos[1],pos[0]+16,pos[1]+16))
        
ws.send('"unsubscribe room:'+shard+'/'+roomName+'"')
ws.close()
bg.save('./screeps-room-'+shard+'-'+roomName+'.png')

