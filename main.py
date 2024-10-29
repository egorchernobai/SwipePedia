import wikipedia
import webbrowser
from colorama import Fore, Back, Style, init
import os

def get_rand(): #Get a random wiki page
	while True:
		wiki = wikipedia.random(pages=1)
		print("Ищем вам интересную статью! Пожалуйста подождите.")
		try:
			wiki_page = wikipedia.page(wiki, preload=True)
			text = wiki_page.content[0:wiki_page.content.find('\n')] #crop from all text on the page to first '\n'
			global url
			url = wiki_page.url #get url of page
			print(' ')
			print(Back.WHITE + Fore.BLACK + wiki) #print name of page
			print(Style.RESET_ALL)
			print(Back.WHITE + Fore.BLACK + text) #and some text of this page
			break
		
		except:
			os.system('cls')
			continue


wikipedia.set_lang('ru') #lang, if you wanna get page of the lang write this: wikipedia.laguage()(so maybe its dont work because i dont remeber true command)
init() #init the colorama
otvet = 0
while otvet !=	1:
	get_rand()
	print(Style.RESET_ALL)
	print("Понравилась?")
	print("[1]Да [2]Нет")
	otvet = int(input())
	if otvet == 2:
		os.system('cls')
		continue
	elif otvet == 1:
		break
webbrowser.open(url, new=0)
