# -*- coding: utf-8 -*-
import json
import os

class pyInit():
	import os
	import json
	
	def process(self,content,pyContent):

		fileName = 'd_card_dis.py.datas.json'

		serverOriPath = 'F:\\kbe\\server\\assets\\scripts\\'
		clientOriPath = 'C:\\Users\\Firesuiry\\Documents\\MyLoserProject\\Assets\\Script\\KBE\\card\\'

		if not os.path.exists(serverOriPath):
			serverOriPath = 'D:\\develop\\server\\KBE\\assets\\scripts\\'

		if not os.path.exists(clientOriPath):
			clientOriPath = 'D:\\develop\\unityProject\\Assets\\Script\\KBE\\card'

		path =  serverOriPath + 'cell\\'
		self.xmlFile = serverOriPath +'entities.xml'
		self.csFilePath = clientOriPath
		self.defPath = serverOriPath + 'entity_defs'

		cs = open('z3.cs', encoding='utf-8')
		self.csContent = cs.read()
		cs.close()

		deff = open('z4.def', encoding='utf-8')
		self.defContent = deff.read()
		deff.close()


		for id in content:
			msg = ('即将检查id:'+str(id))
			print(msg)
			name=('card_'+ str(id))
			
			pyfileName = name + '.py'
			pyfile = os.path.join(path,pyfileName)
			pytarcontent = pyContent
			pytarcontent = pytarcontent.replace('card_CHANGEIDSPACE',name)
			pytarcontent = pytarcontent.replace('CARDNAMESPACE',content[id].get('name',''))
			pytarcontent = pytarcontent.replace('CARDDESSPACE',content[id].get('des',''))

			self.writeFile(name+'.py',pyfile,pytarcontent)
			

	def writeFile(self,name,pyfile,content):
		if not os.path.exists(pyfile):
			fp = open(pyfile,'w',encoding='utf-8')
			contents = content.split(r'\n')
			fp.writelines(contents)
			fp.close()

		print(name)
		csFile = os.path.join(self.csFilePath,name.replace('.py','.cs'))
		if not os.path.exists(csFile):
			fp3 = open(csFile,'w',encoding = 'utf-8')
			csc = self.csContent.replace('Avatar',name)
			csc = csc.replace('.py','')
			fp3.writelines(csc.split(r'\n'))
			fp3.close()

		defFile = os.path.join(self.defPath,name.replace('.py','.def'))
		if not os.path.exists(defFile):
			fp3 = open(defFile,'w',encoding = 'utf-8')
			fp3.writelines(self.defContent.split(r'\n'))
			fp3.close()


		fp2 = open(self.xmlFile,'r',encoding='utf-8')
		content3 = fp2.read()
		fp2.close()

		fp2 = open(self.xmlFile,'a+',encoding='utf-8')
		content2 = '<Avatar hasClient="true"></Avatar>\n'
		content2 = content2.replace('Avatar',name)
		content2 = content2.replace('.py','')		
		if not content2 in content3:
			#print(not content2 in content3)
			pp = [content2]
			fp2.writelines(pp)
		fp2.close()


fileName = 'd_card_dis.py.datas.json'

f = open(fileName, encoding='utf-8')
content = json.load(f)

file_object = open('z2.py',mode='r', encoding='UTF-8')
pyFileContent = ''
try:
     pyFileContent = file_object.read()
finally:
     file_object.close( )
if pyFileContent == '':
	print('py文件读取失败')
else:
	print('py文件读取完成 开始写入')
	print(pyFileContent)
	print(type(pyFileContent))
	py1 = pyInit()
	py1.process(content,pyFileContent)


