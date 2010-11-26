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



function FSHttpStream(host, port, path, onMessage, onOpen, onClose, filters) {
  if ((!port) || (port == null) || (port == "")) { 
    this.address = host;
  } else {
    this.address = host + ":"+port;
  }
  if (path) {
    this.address = this.address + path;
  }
  this.mode = 0;
  this.url = "";
  this.sock = null;

  this.onMessage = onMessage;
  this.onOpen = onOpen;
  this.onClose = onClose;

  this.filter = new ClientEventFilter(filters);

  if (!window.WebSocket) {
    this.mode = -1;
    alert("Websocket not supported !");
    return false;
  } else {
    this.mode = 1;
  }
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
}

FSHttpStream.prototype.Bind = function(func) {
  var obj = this;
  return function() {
    return func.apply(obj, arguments);
  }
}

function has_websocket() {
  if (!window.WebSocket) { return false; }
  return true;
}

FSHttpStream.prototype.getMode = function() {
  return this.mode;
};
  
FSHttpStream.prototype.getStringMode = function() {
  if (this.mode == 1) {
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



