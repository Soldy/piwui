#!/usr/bin/python

import osonsql


osondbcon = osonsql.connect("sqlite", "db/file.db")
tableaccesn = ("id", "filepath", "filename", "filetype", "filesize", "fileaudioform", "fileaudiobit", "fileaudiorate", "fileaudiochannel", "fileaudiolangs", "filevideoformat", "filevideobit", "filevideoresult", "filevideofps", "filevideoaspect", "filelength", "fileseekable", "filechapters", "filemd5", "fileid") 
tableaccest = ("text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text", "text")
tableaccess = (0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0)
osonsql.make("sqlite", osondbcon, "files", tableaccesn, tableaccest, tableaccess)
osonsql.close("sqlite", osondbcon)
osondbcon = osonsql.connect("sqlite", "db/passwd.db")
tableaccesn = ("id", "userid", "username", "password") 
tableaccest = ("text", "text", "text", "text")
tableaccess = (0, 0, 0, 0)
osonsql.make("sqlite", osondbcon, "passwd", tableaccesn, tableaccest, tableaccess)
osonsql.close("sqlite", osondbcon)