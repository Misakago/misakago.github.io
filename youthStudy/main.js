main = document.getElementById('main');
wrapper = document.getElementById('wrapper');
level1 = ['地市', '直属高校', '直属企业团委', '省直团工委', '省国资委团工委', '独立院校', '各直接联系组织', '系统团委', '其他团组织'];
//获取 cookie 值
function getCookie(cname) {
    var name = cname + "=";
    var ca = document.cookie.split(';');
    for (var i = 0; i < ca.length; i++) {
        var c = ca[i].trim();
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return "";
}
//判断是否显示协议
if (getCookie('isagree') === 'true'){
    wrapper.remove();
    add_level(level1);
}
// 同意协议             
function agree() {
    checkbox = document.getElementById('checkbox');
    if (checkbox.checked) {
        
        var opacity = 1;
        var timer = null;
        timer = setInterval(function () {
            opacity = opacity - 0.05;
            if (opacity > 0) {
                document.getElementById('wrapper').style.opacity = opacity;
            } else {
                document.getElementById('wrapper').style.opacity = 0;
                wrapper.remove();
                document.cookie = "isagree=true";
                add_level(level1);
                clearInterval(timer);
            }
        }, 20);
    } else {
        alert('请勾选“我已阅读并同意以上协议”！')
    }

}
// 添加level
function add_level(level) {
    info = document.getElementById('info');
    for (var i = 0; i < level1.length; i++) {
        var org = document.createElement('p');
        org.innerHTML = level1[i];
        info.appendChild(org);
    }
}

document.getElementById('info').addEventListener('click',evt => {
    let request = new XMLHttpRequest();
    request.onload = function(evt){
        let xhr = evt.target;
        if(xhr.status === 200){
            // document.getElementById('info').innerHTML = xhr.responseText;
            alert(xhr.responseText);
        }
    };
    let url = `http://dxx.ahyouth.org.cn/api/peopleRankList?level1=${evt.target.innerHTML}`;
    request.open('GET',url);
    request.send()
})
