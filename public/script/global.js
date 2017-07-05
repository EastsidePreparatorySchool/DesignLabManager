function logout() {
    document.cookie = 'auth=; expires=Thu, 01 Jan 1970 00:00:01 GMT;';
    location.reload();
}
function login() { //Takes either login, register, or resend
    var data = new FormData(),
        email = document.getElementById('login_email'),
        password = document.getElementById('login_pass');
    
    
    data.append('email', email.value);
    data.append('password', password.value);

    xhr = new XMLHttpRequest();
    xhr.onreadystatechange = function() {
        if (xhr.readyState == 4 && xhr.status == 200) {
            result = xhr.responseText;
            if (result == '') location.reload();
            else alert(result);
        } else alert('We\'re not sure what went wrong');
    }
    xhr.open('POST', '/login', true);
    xhr.send(data);
}

function alert(t) {
    window.alert(t);
}