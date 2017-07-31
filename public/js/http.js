function HttpClient() {
  this.convert = (params) => {
    let fd = new FormData();
    for (let i = 0; i < Object.keys(params).length; i++) {
      key = Object.keys(params)[i]
      fd.append(key, String(params[key]));
    }
    return fd;
  };
  this.xhr = (type, url, callback, params) => {
    let httpRequest = new XMLHttpRequest();
    httpRequest.onreadystatechange = () => {callback(httpRequest)}
    httpRequest.open(type, url, true);
    httpRequest.send(params);
  };
  this.get = (url, callback) => this.xhr('GET', url, callback, null);
  this.post = (url, params, callback) => this.xhr('POST', url, callback, this.convert(params));
  this.put = (url, params, callback) => this.xhr('PUT', url, callback, this.convert(params));
  this.delete = (url, params, callback) => this.xhr('DELETE', url, callback, this.convert(params));
}
