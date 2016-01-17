import requests
import multiprocessing
import json
import os
import random
import glob

url="http://localhost:7474/db/data/cypher"
headers={"content-type":"application/json"}
st=[]
def playMusic():
	l=glob.glob("/Users/RISHAV/Desktop/videos/*.mp4")
	play=random.choice(l)
	os.system("afplay '"+play+"'")
def respond(di):
	instruction=di["instruction"]
	metadata=di["metadata"]
	person=metadata["person"]
	location=metadata["message"]
	print location
	print person
	ins=instruction.split(" ")
	l=len(ins)
	query="match n where "
	if False:
		os.system("espeak 'I am a machine.. I will always be fine !'")
	else:
		for i in range(l-1):
			m="'"+ins[i]+"' in n.words"
			query+=m
			query+=" or "
		m="'"+ins[l-1]+"' in n.words return id(n) order by id(n) desc"
		query+=m
		q={"query":query}
		response=requests.post(url,data=json.dumps(q),headers=headers).json()['data']
		for i in response:
			res=i[0]
			if res==26043:
				message="I am holmie,I am an AI. I contain some features such as playing music, suggesting movies, describing things and person I see or anyone asks. I hope you enjoy interacting with me"
				os.system("espeak '"+message+"'")
			elif res==26042:
				os.system("espeak 'you are "+person+"'")
				os.system(location)
			elif res==26040:
				if len(st)==0:
					p=multiprocessing.Process(target=playMusic)
					st.append(p)
					p.start()
				else:
					p=st.pop()
					p.terminate()
					p1=multiprocessing.Process(playMusic)
					st.append(p1)
					p1.start()



if __name__=="__main__":
	respond("who are you")
