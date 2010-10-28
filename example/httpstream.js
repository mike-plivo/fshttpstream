function HttpStream(url, onmessage, onopen, onclose, checkinterval) {
  this.url = url;
  this.checkinterval = 100;
  this._flushPatt = /Flush-Browser-Buffer/;
  this._bufferPos = 0;

  if (checkinterval)
    this.checkinterval = checkinterval;

  // set callbacks
  this.onmessage = onmessage;
  this.onclose = onclose;
  this.onopen = onopen;

  // create xhr
  this.xhr = this.createXMLHttpRequest();

  // now do request
  this.xhr.open("GET", this.url, true);
  if (this.onopen) {
    this.onopen();
  }
  this.xhr.send(null);

  this.timer = setInterval(this.Bind(function() {
                                        if (!this.xhr)
                                          return;
                                        if (this.xhr.readyState == 4) {
                                          clearInterval(this.timer);
                                          this.onclose();
                                          return;
                                        }
                                        var buffer = null;
                                        var unparsed = null;
                                        do {
                                          buffer = this.xhr.responseText;
                                          unparsed = buffer.substring(this._bufferPos);
                                          var msgEndIndex = unparsed.indexOf("\r\n\r\n");
                                          if (msgEndIndex != -1) {
                                            var msgEndOfFirstIndex = msgEndIndex + "\r\n\r\n".length;
                                            var msg = unparsed.substring(0, msgEndOfFirstIndex);
                                            var newmsg = msg.replace(/(.*)\r\n\r\n/, "$1");
                                            if ((this.onmessage) && (!newmsg.match(this._flushPatt))) {
                                              this.onmessage(newmsg);
                                            }
                                            this._bufferPos += msgEndOfFirstIndex;
                                            
                                          }
                                        } while (msgEndIndex != -1);
                                        buffer = null;
                                        unparsed = null;
                                      }), 
                                     this.checkinterval
                          );


}

HttpStream.prototype.Bind = function(func) {
  var obj = this;
  return function() {
    return func.apply(obj, arguments);
  }
}

HttpStream.prototype.trim = function(str) {
  return str.replace(/(^\s+|\s+$)/g,'');
}

HttpStream.prototype.createXMLHttpRequest = function() {
    xhr = null;
    try {
      xhr = new ActiveXObject("Microsoft.XMLHTTP");
    } catch(e) {
      xhr = new XMLHttpRequest();
    }
    if (!xhr) { alert('Ajax not supported !'); }
    return xhr;
};

