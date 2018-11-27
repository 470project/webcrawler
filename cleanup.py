import json
import jsonlines

entities = []

with open('result.jl') as f:  
    cnt = 0
    for line in f:
        j = json.loads(line)
        if j["pageType"] == "user":
            item = {
                'pT':j["pageType"],
                'name':j['name'],
                'stories':j['stories']
                }
            favs = []
            for fav in j["favorites"]:
                favs.append({'S':fav['favStory'],'A':fav['favAuthor']})
            item['favorites'] = favs
            entities.append(item)

        if j["pageType"] == "story":
            favs = int(j["otherInfo"]["favorites"])
            author = j["author"]
            link = j["storyLink"]
            
            item = {
                'pT':j["pageType"],
                'storyLink':j["storyLink"],
                'favorites':j["otherInfo"]["favorites"],
                'author': j["author"],
                'otherInfo':{'favorites':j["otherInfo"]["favorites"]}
                } 
            entities.append(item)
        
        if j["pageType"] == "review":
            item = {
                'pT':j["pageType"],
                'rO': j['reviewOf'],
                'r': j['reviewer'],
                'sS': j['sentimentScore'],
                }
            entities.append(item)
print(len(entities))
with jsonlines.open('resultCleanup.jl', mode='w') as writer:
    for entity in entities:
        writer.write(entity)