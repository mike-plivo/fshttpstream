function makeFilter(filters) {
    if (!filters) {
      return "";
    }
    var encoded_filters = "";
    var i = 0;
    for (i=0; i<filters.length; i++) {
       if (i>0) {
         encoded_filters += "&filter="+encodeURIComponent(filters[i]);
       } else {
         encoded_filters += "filter="+encodeURIComponent(filters[i]);
       }
    }
    return encoded_filters;
}


