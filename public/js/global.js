const httpClient = new HttpClient();

function logout() {
  document.cookie = 'auth=; expires=Thu, 01 Jan 1970 00:00:01 GMT; path=/';
  location.reload();
}
function login() {
  emailhandle = document.getElementById('email'),
  passwordhandle = document.getElementById('password');

  httpClient.post("/login", {
    email: emailhandle.value,
    password: passwordhandle.value
  }, (hr) => {
    if (hr.readyState == 4 && hr.status == 200) {
      if (hr.responseText == "") location.reload();
      else window.alert(hr.responseText);
    }
  });
}



$(window).scroll(function () {
  $(".main-nav").css("opacity", 1 - $(window).scrollTop() / 1600);
});
