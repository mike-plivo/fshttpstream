function HttpStream(fs, url, onmessage, onopen, onclose, checkinterval) {
  this.fs = fs;
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
  this.state = 0;

  // create xhr
  this.xhr = this.createXMLHttpRequest();

  // now do request
  this.xhr.open("GET", this.url, true);
  this.state = 1;
  if (this.onopen) {
    this.onopen(this.fs);
  }
  this.xhr.send(null);

  this.timer = setInterval(this.Bind(function() {
                                        if (!this.xhr)
                                          return;
                                        if (this.xhr.readyState == 4) {
                                          clearInterval(this.timer);
                                          this.state = 0;
                                          this.onclose(this.fs);
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
                                              this.onmessage(this.fs, newmsg);
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

HttpStream.prototype.getState = function() {
  return this.state;
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



function ClientEventFilter(filters) {
    this.filters = filters;
    this.encoded_filters = "";
    this.string_filters = ""

    if ((!this.filters) || (this.filters.length == 0)) {
      this.filters = [];
      this.encoded_filters = "";
      this.string_filters = ""
    } else {
      var i = 0;
      for (i=0; i<this.filters.length; i++) {
         if (i>0) {
           this.string_filters += ", '"+filters[i]+"'";
           this.encoded_filters += "&filter="+encodeURIComponent(filters[i]);
         } else {
           this.string_filters += "'"+filters[i]+"'";
           this.encoded_filters += "?filter="+encodeURIComponent(filters[i]);
         }
      }
    }

    this.getEncodedFilters = function() {
      return this.encoded_filters;
    };
    this.getStringFilters = function() {
      return this.string_filters;
    };
    this.getArrayFilters = function() {
      return this.filters;
    };
}



function FSHttpStream(host, port, onMessage, onOpen, onClose, filters) {
  this.address = host + ":"+port;
  this.mode = 0;
  this.url = "";
  this.sock = null;

  this.onMessage = onMessage;
  this.onOpen = onOpen;
  this.onClose = onClose;

  this.filter = new ClientEventFilter(filters);

  //if (!window.WebSocket) {
    this.mode = 1;
    this.url = "http://" + this.address + "/stream" + this.filter.getEncodedFilters();
    this.sock = new HttpStream(this, this.url, this.onMessage, this.onOpen, this.onClose);
  /*} else {
    this.mode = 2;
    this.ws_state = 0;
    this.url = "ws://" + this.address + "/websock" + this.filter.getEncodedFilters(); 
    this.sock = new WebSocket(this.url);
    this.sock.onmessage = this.Bind(function(e) {
      this.onMessage(this, e.data);
    });
    this.sock.onopen = this.Bind(function(e) {
      this.ws_state = 1;
      this.onOpen(this);
    });
    this.sock.onclose = this.Bind(function(e) {
      this.ws_state = 0;
      this.onClose(this);
    });
  }*/
}

FSHttpStream.prototype.Bind = function(func) {
  var obj = this;
  return function() {
    return func.apply(obj, arguments);
  }
}

/*
// not working this.sock is always null :(

FSHttpStream.prototype.getState = function() {
  if (this.mode == 1) {
    if (!this.sock) {
      return 0;
    }
    return this.sock.getState();
  } else if (this.mode == 2) {
    return this.ws_state;
  }
  return 0;
};
  
FSHttpStream.prototype.getStringState = function() {
  var state = 0;
  if (this.mode == 1) {
    if (!this.sock) {
      return "DOWN";
    } else {
      state = this.sock.getState();
    }
  } else if (this.mode == 2) {
    state = this.ws_state;
  }
  if (state == 1) {
    return "UP";
  }
  return "DOWN";
};
*/

FSHttpStream.prototype.getMode = function() {
  return this.mode;
};
  
FSHttpStream.prototype.getStringMode = function() {
  if (this.mode == 1) {
    return "HttpStream";
  } else if (this.mode == 2) {
    return "WebSocket";
  }
  return "NotSupported";
};

FSHttpStream.prototype.getStringFilters = function() {
  return this.filter.getStringFilters();
};

FSHttpStream.prototype.getEncodedFilters = function() {
  return this.filter.getEncodedFilters();
};

FSHttpStream.prototype.getArrayFilters = function() {
  return this.filter.getEncodedFilters();
};

FSHttpStream.prototype.getFilters = function() {
  return this.filter;
};

FSHttpStream.prototype.getUrl = function() {
  return this.url;
};

FSHttpStream.prototype.getAddress = function() {
  return this.address;
};



