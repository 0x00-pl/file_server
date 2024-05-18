import os
import sys
import io
import http.server
import argparse
import html
import urllib.parse
import base64


class myioHander(http.server.SimpleHTTPRequestHandler):
    def do_POST(self):
        """Serve a POST request."""
        if self.path.endswith('/'):
            print('---POST---')
            length= int(self.headers.get('content-length'))
            reqpath= self.translate_path(self.path)

            name= self.headers.get('upload-filename')
            #decode name
            name= name.encode('iso-8859-1').decode()
            
            path= os.path.join(reqpath,name)
            if name.endswith('/'):
                os.makedirs(path)
                print('create dir',path)
            else:
                ofile= open(path,'bw')
                ofile.write(self.rfile.read(length))
                ofile.close()
                print('create file',path)
            print('+++POST+++')
            
        f = self.send_head()
        if f:
            self.copyfile(f, self.wfile)
            f.close()


    def send_head(self):
        """Common code for GET and HEAD commands.

        This sends the response code and MIME headers.

        Return value is either a file object (which has to be copied
        to the outputfile by the caller unless the command was HEAD,
        and must be closed by the caller under all circumstances), or
        None, in which case the caller has nothing further to do.

        """
        path = self.translate_path(self.path)
        f = None
        if os.path.isdir(path):
            if not self.path.endswith('/'):
                # redirect browser - doing basically what apache does
                self.send_response(301)
                self.send_header("Location", self.path + "/")
                self.end_headers()
                return None
            for index in "index.html", "index.htm":
                index = os.path.join(path, index)
                if os.path.exists(index):
                    path = index
                    break
            else:
                return self.list_directory(path)
        ctype = self.guess_type(path)
        try:
            f = open(path, 'rb')
        except IOError:
            self.send_error(404, "File not found")
            return None
        self.send_response(200)
        self.send_header("Content-type", ctype)
        fs = os.fstat(f.fileno())
        self.send_header("Content-Length", str(fs[6]))
        self.send_header("Last-Modified", self.date_time_string(fs.st_mtime))
        self.end_headers()
        return f
    def list_directory(self, path):
        """Helper to produce a directory listing (absent index.html).

        Return value is either a file object, or None (indicating an
        error).  In either case, the headers are sent, making the
        interface the same as for send_head().

        """
        try:
            list = os.listdir(path)
        except os.error:
            self.send_error(404, "No permission to list directory")
            return None
        list.sort(key=lambda a: a.lower())
        r = []
        displaypath = html.escape(urllib.parse.unquote(self.path))
        enc = sys.getfilesystemencoding()
        title = 'Directory listing for %s' % displaypath
        r.append('<!DOCTYPE HTML PUBLIC "-//W3C//DTD HTML 4.01//EN" '
                 '"http://www.w3.org/TR/html4/strict.dtd">')
        r.append('<html>\n<head>')
        r.append('<meta http-equiv="Content-Type" '
                 'content="text/html; charset=%s">' % enc)
        r.append('<title>%s</title>\n</head>' % title)
        r.append('<body>\n<h1>%s</h1>' % title)
        r.append('<hr>\n<ul>')
        for name in list:
            fullname = os.path.join(path, name)
            displayname = linkname = name
            # Append / for directories or @ for symbolic links
            if os.path.isdir(fullname):
                displayname = name + "/"
                linkname = name + "/"
            if os.path.islink(fullname):
                displayname = name + "@"
                # Note: a link to a directory displays with @ and links with /
            r.append('<li><a href="%s">%s</a></li>'
                    % (urllib.parse.quote(linkname), html.escape(displayname)))
        r.append('</ul>\n<hr>\n')
        '''--------'''
        r.append('<div id="container">FILE <div id="file_list"></div></div>\n')
        r.append('<script>\n'+
'''
// Check for the various File API support.
if (window.File && window.FileReader && window.FileList && window.Blob) {
  // Great success! All the File APIs are supported.
} else {
  alert('The File APIs are not fully supported in this browser.');
}

function handleDrop(evt){
    //阻止默认事件
    evt.stopPropagation();
    evt.preventDefault();
    var files = evt.dataTransfer.items;
    for(var i=0,f;f=files[i];i++){
        uploadFile(f,document.getElementById('file_list'));
    }
}

 function uploadFile(file, progressbar) 
 { 
 var xhr = new XMLHttpRequest(); 
 var upload = xhr.upload; 

 var p = document.createElement('p'); 
 p.textContent = "0%";
 p.style.width = "200px";
 p.style.background = "blue";
 p.style.color = "yellow";
 progressbar.appendChild(p); 
 upload.progressbar = progressbar; 
 // 设置上传文件相关的事件处理函数
 upload.addEventListener("progress", uploadProgress, false); 
 upload.addEventListener("load", uploadSucceed, false); 
 upload.addEventListener("error", uploadError, false);
 
 // 上传文件

 var isdir=false;
 var name=file.getAsFile().name;
 if(file.getAsEntry){
  isdir=file.getAsEntry().isDirectory;
 }else if(file.webkitGetAsEntry){
  isdir=file.webkitGetAsEntry().isDirectory;
 }else if(file.isDirectory!==undefined){
  isdir=file.isDirectory;
 }else{
  alert("不能检测是否为文件夹")
  isdir=(file.size==0)
 }
 xhr.open("POST", "",true);
 xhr.setRequestHeader("upload-filename", name+(isdir?"/":""));
 xhr.send(file.getAsFile());
 }
 
 function uploadProgress(event) 
 { 
 if (event.lengthComputable) 
 { 
    // 将进度换算成百分比
 var percentage = Math.round((event.loaded * 100) / event.total); 
 //console.log("percentage:" + percentage); 
 if (percentage < 100) 
 { 
 event.target.progressbar.firstChild.style.width = (percentage*2) + "px"; 
 event.target.progressbar.firstChild.textContent = percentage + "%"; 
 } 
 } 
 }
 
 function uploadSucceed(event) 
 { 
 event.target.progressbar.firstChild.style.width = "200px"; 
 event.target.progressbar.firstChild.textContent = "100%"; 
 }
 
 function uploadError(error) 
 { 
 alert("error: " + error); 
 } 

document.getElementById("container");
 // 拖拽结束时触发
container.addEventListener("drop", handleDrop, false);
 // 拖拽进入目标对象时触发
 container.addEventListener("dragenter", function(event) 
 { 
 event.stopPropagation(); 
 event.preventDefault(); 
 }, false); 
 // 拖拽在目标对象上时触发
 container.addEventListener("dragover", function(event) 
 { 
 event.stopPropagation(); 
 event.preventDefault(); 
 }, false); 
'''+'</script>\n')
        '''--------'''
        r.append('</body>\n</html>\n')
        encoded = '\n'.join(r).encode(enc)
        f = io.BytesIO()
        f.write(encoded)
        f.seek(0)
        self.send_response(200)
        self.send_header("Content-type", "text/html; charset=%s" % enc)
        self.send_header("Content-Length", str(len(encoded)))
        self.end_headers()
        return f

def test(HandlerClass = myioHander,
         ServerClass = http.server.HTTPServer, protocol="HTTP/1.0", port=80):
    """Test the HTTP request handler class.

    This runs an HTTP server on port 8000 (or the first command line
    argument).

    """
    server_address = ('', port)

    HandlerClass.protocol_version = protocol
    httpd = ServerClass(server_address, HandlerClass)

    sa = httpd.socket.getsockname()
    print("Serving HTTP on", sa[0], "port", sa[1], "...")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        print("\nKeyboard interrupt received, exiting.")
        httpd.server_close()
        sys.exit(0)

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--cgi', action='store_true',
                       help='Run as CGI Server')
    parser.add_argument('port', action='store',
                        default=80, type=int,
                        nargs='?',
                        help='Specify alternate port [default: 8000]')
    args = parser.parse_args()
    test(HandlerClass=myioHander, port=args.port)

