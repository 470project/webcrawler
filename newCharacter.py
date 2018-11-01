import json
#old code lines 22-23 and 204-210
with open('harryPotterCharacters.json') as f:
    characters = [x.lower() for x in json.load(f)["characters"]]

#find relevant characters
characterFreq = {}
for character in characters:
    if(character in text):
        if(character not in characterFreq):
			characterFreq[character] = 0
    characterFreq[character] += text.count(character)
	

#new code
import json
from collections import defaultdict
with open('longListHarryPotterCharacters.json') as f:
    jsonCharacters = json.load(f)["characters"]
    characters = defaultdict(list)
    for character in jsonCharacters:  
        for name in jsonCharacters[character]:
            characters[character].append(name.lower())
	
#find relevant characters
characterFreq = {}
for character, names in characters.items():
	for name in names:
		if(name in text):
			if(character not in characterFreq):
				characterFreq[character] = 0
			characterFreq[character] += text.count(name)	