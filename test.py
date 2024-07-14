from py7zr import SevenZipFile
archive7z = SevenZipFile('test.7z', mode='r', password='test')
filenames = archive7z.getnames()
infos = archive7z.list()
info = infos[0]
for p, v in vars(info).items():
	print(p, v)
print(info.creationtime, type(info.creationtime))