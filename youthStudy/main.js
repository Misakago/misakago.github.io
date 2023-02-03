let main = document.getElementById('main');
let wrapper = document.getElementById('wrapper');
let level1 = ['level1', '地市', '直属高校', '直属企业团委', '省直团工委', '省国资委团工委', '独立院校', '各直接联系组织', '系统团委', '其他团组织'];
let base_url = 'http://dxx.ahyouth.org.cn/api/peopleRankStage?table_name=reason_stage239';
let saved_url = ''
let table_name = {};
let now = [];
let all = [];
//获取table_name
window.onload = function () {
    let request = new XMLHttpRequest();
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            let data = JSON.parse(xhr.responseText)['list'];
            for (let i = 0; i < 10; i++) {
                table_name[`${data[i]['table_name']}`] = `${data[i]['name']}`;
            }
        }
    };
    let url = 'http://dxx.ahyouth.org.cn/api/peopleRankList';
    request.open('GET', url);
    request.send();

    saved_url = get_cookie('url');
    let table_name1 = get_cookie('table_name');

    let request1 = new XMLHttpRequest();
    request1.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            let data = JSON.parse(xhr.responseText)['list']['list'];
            for (let i = 1; i < data.length; i++) {
                all.push(data[i]['username']);
            }
        }
    };
    let url1 = saved_url.replace('reason_stage239', table_name1);
    request1.open('GET', url1);
    request1.send();

    //判断是否显示协议
    if (get_cookie('isagree') === 'true') {
        wrapper.remove();
        if (get_cookie('url') === '') {
            document.getElementById('info').style.display = 'block';
            add_level(level1);
        } else {
            document.getElementById('menu').style.display = 'block';
        }
    }
}

//复制到剪贴板
function copyToClip(contentArray, message) {
    var contents = "";
    for (var i = 0; i < contentArray.length; i++) {
        contents += contentArray[i] + "\n";
    }
    contents += '嗨，我正在使用团支书小助手，你也来试试吧！\n下载链接：https://consider.lanzoub.com/is4VH0miy0di'
    const textarea = document.createElement('textarea');
    textarea.value = contents;
    document.body.appendChild(textarea);
    textarea.select();
    if (document.execCommand('copy')) {
        document.execCommand('copy');
    }
    document.body.removeChild(textarea);
    if (message == null) {
        alert("复制成功！\n期待您的推荐！");
    } else {
        alert(message);
    }
}

//获取 cookie 值
function get_cookie(cname) {
    let name = cname + "=";
    let ca = document.cookie.split(';');
    for (let i = 0; i < ca.length; i++) {
        let c = ca[i].trim();
        if (c.indexOf(name) == 0) return c.substring(name.length, c.length);
    }
    return "";
}

//清除cookie
function clear_cookie() {
    document.cookie = "isagree=false";
    location.reload();
}

//移除子节点
function empty(e) {
    while (e.firstChild) {
        e.removeChild(e.firstChild);
    }
}

//显示结果
function show_result() {
    let request = new XMLHttpRequest();
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            data = JSON.parse(xhr.responseText)['list']['list'];
            for (let i = 1; i < data.length; i++) {
                now.push(data[i]['username']);
            }
            let minus = arrayAminusB(all, now);
            if (minus === []){
                alert('全员完成！')
            }else{
                result = document.getElementById('result');
                empty(result);
                for (let i = 0; i < minus.length; i++) {
                    let name = document.createElement('p');
                    name.innerHTML = minus[i];
                    result.appendChild(name);
                }
                copyToClip(minus);
            }
        };
        let url2 = saved_url.replace('reason_stage239', Object.keys(table_name)[0]);
        request.open('GET', url2);
        request.send();

    }
}

//求差集
function arrayAminusB(arrA, arrB) {
    return arrA.filter(v => !arrB.includes(v));
}

// 同意协议             
function agree() {
    checkbox = document.getElementById('checkbox');
    if (checkbox.checked) {

        let opacity = 1;
        let timer = null;
        timer = setInterval(function () {
            opacity = opacity - 0.05;
            if (opacity > 0) {
                document.getElementById('wrapper').style.opacity = opacity;
            } else {
                document.getElementById('wrapper').style.opacity = 0;
                wrapper.remove();
                document.cookie = "isagree=true";
                document.getElementById('info').style.display = 'block';
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
    let level_tag = document.getElementById(`${level[0]}`);
    for (let i = 1; i < level.length; i++) {
        let org = document.createElement('p');
        org.innerHTML = level[i];
        level_tag.appendChild(org);
    }
}

//level1点击事件
document.getElementById('level1').addEventListener('click', evt => {
    let request = new XMLHttpRequest();
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            data = JSON.parse(xhr.responseText)['list']['list'];
            let level2 = ['level2'];
            for (let i = 1; i < data.length; i++) {
                level2.push(data[i]['level2']);
            }
            add_level(level2);
        }
    };
    let url = base_url + `&level1=${evt.target.innerHTML}`;
    base_url = url;
    let navigation = document.getElementById('navigation');
    let level1 = document.createElement('span');
    level1.innerHTML = evt.target.innerHTML + '/';
    navigation.appendChild(level1);
    document.getElementById('level1').remove();
    request.open('GET', url);
    request.send();
})

//level2点击事件
document.getElementById('level2').addEventListener('click', evt => {
    let request = new XMLHttpRequest();
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            data = JSON.parse(xhr.responseText)['list']['list']
            if (data[0]['username'] !== undefined) {
                for (key in table_name) {
                    get_num(key);
                }
                alert('请选择全员完成的一期！')
            } else {
                let level3 = ['level3'];
                for (let i = 1; i < data.length; i++) {
                    level3.push(data[i]['level3']);
                }
                add_level(level3);
            }
        }
    };
    let url = base_url + `&level2=${evt.target.innerHTML}`;
    base_url = url;
    let navigation = document.getElementById('navigation');
    let level2 = document.createElement('span');
    level2.innerHTML = evt.target.innerHTML + '/';
    navigation.appendChild(level2);
    document.getElementById('level2').remove();
    request.open('GET', url);
    request.send();
})

//level3点击事件
document.getElementById('level3').addEventListener('click', evt => {
    let request = new XMLHttpRequest();
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            data = JSON.parse(xhr.responseText)['list']['list']
            if (data[0]['username'] !== undefined) {
                for (key in table_name) {
                    get_num(key);
                }
                alert('请选择全员完成的一期！')
            } else {
                let level4 = ['level4'];
                for (let i = 1; i < data.length; i++) {
                    level4.push(data[i]['level4']);
                }
                add_level(level4);
            }
        }
    };
    let url = base_url + `&level3=${evt.target.innerHTML}`;
    base_url = url;
    let navigation = document.getElementById('navigation');
    let level3 = document.createElement('span');
    level3.innerHTML = evt.target.innerHTML + '/';
    navigation.appendChild(level3);
    document.getElementById('level3').remove();
    request.open('GET', url);
    request.send();
})

//level4点击事件
document.getElementById('level4').addEventListener('click', evt => {
    let request = new XMLHttpRequest();
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            data = JSON.parse(xhr.responseText)['list']['list']
            if (data[0]['username'] !== undefined) {
                for (key in table_name) {
                    get_num(key);
                }
                alert('请选择全员完成的一期！')
            } else {
                let level5 = ['level5'];
                for (let i = 1; i < data.length; i++) {
                    level5.push(data[i]['level5'])
                }
                add_level(level5);
            }
        }
    };
    let url = base_url + `&level4=${evt.target.innerHTML}`;
    base_url = url;
    let navigation = document.getElementById('navigation');
    let level4 = document.createElement('span');
    level4.innerHTML = evt.target.innerHTML + '/';
    navigation.appendChild(level4);
    document.getElementById('level4').remove();
    request.open('GET', url);
    request.send();
})

//level5点击事件
document.getElementById('level5').addEventListener('click', evt => {
    let request = new XMLHttpRequest();
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            data = JSON.parse(xhr.responseText)['list']['list']
            for (key in table_name) {
                get_num(key);
            }
            alert('请选择全员完成的一期！')
        }
    }
    let url = base_url + `&level5=${evt.target.innerHTML}`;
    base_url = url;
    let navigation = document.getElementById('navigation');
    let level5 = document.createElement('span');
    level5.innerHTML = evt.target.innerHTML + '/';
    navigation.appendChild(level5);
    document.getElementById('level5').remove();
    request.open('GET', url);
    request.send();
})

//reason点击事件
document.getElementById('reason').addEventListener('click', evt => {
    document.cookie = `url=${base_url}`;
    document.cookie = `table_name=${evt.target.id}`;
    alert('选择成功！');
    location.reload();
})

//获取人数
function get_num(key) {
    url = base_url.replace('reason_stage239', key);
    let request = new XMLHttpRequest();
    let reason = document.getElementById('reason')
    request.onload = function (evt) {
        let xhr = evt.target;
        if (xhr.status === 200) {
            let num = JSON.parse(xhr.responseText)['list']['list'];
            let msg = table_name[key] + ' ' + num.length + '人';
            let tag = document.createElement('p');
            tag.id = key;
            tag.innerHTML = msg;
            reason.appendChild(tag);
        }
    }
    request.open('GET', url);
    request.send();
}
