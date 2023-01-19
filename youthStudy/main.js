var txt = "<center><div class ='title'><h3>确认信息</h3></div><input type='text' name='level1' id='level1' readonly='readonly'/><input type='text' name='level2' id='level2' readonly='readonly'/><input type='text' name='level3' id='level3' readonly='readonly'/><input type='text' name='token' id='token' style='display:none'/><textarea id='nameList' name='nameList' required='required'></textarea><input type='button' onclick='getName()' value='获取名单'><br><br><input type='submit' value='提交'></center>"//定义表单

var btn="<input type='button' onclick='submit()' value='开始查询' id='btn'>"//定义按钮

var tableapi = "http://dxx.ahyouth.org.cn/api/peopleRankList"

//var tableName= ""


function submit(){
	
url = 'http://dxx.ahyouth.org.cn/#/pages/class/ranking/ranking?table_name=reason_stage239&level1=%25E7%259B%25B4%25E5%25B1%259E%25E9%25AB%2598%25E6%25A0%25A1&level2=%25E5%2590%2588%25E8%2582%25A5%25E5%25B7%25A5%25E4%25B8%259A%25E5%25A4%25A7%25E5%25AD%25A6&level3=%25E7%2594%25B5%25E6%25B0%2594%25E4%25B8%258E%25E8%2587%25AA%25E5%258A%25A8%25E5%258C%2596%25E5%25B7%25A5%25E7%25A8%258B%25E5%25AD%25A6%25E9%2599%25A2%25E5%259B%25A2%25E5%25A7%2594&level4=%25E7%25A0%2594%25E7%25A9%25B6%25E7%2594%259F2021%25E7%25BA%25A738%25E7%258F%25AD%25E5%259B%25A2%25E6%2594%25AF%25E9%2583%25A8';
levels = getLevels(url)
if(url.search("level4")!=-1){
  document.getElementById("iframe").style = "display:none"
  document.getElementById("btn").style = "display:none"
document.getElementById("form").innerHTML = txt 
document.getElementById('level1').value=decodeURIComponent(levels[1])
document.getElementById('level2').value=decodeURIComponent(levels[2])
document.getElementById('level3').value=decodeURIComponent(levels[3])
document.getElementById('token').value=createToken()

}
}//校验并生成提交页面

function createButton(id)
{
document.getElementById(id).innerHTML= btn
}//在iframe加载完毕时执行按钮创建

function getLevels(url){
    level = url
    
    index1 = url.indexOf("&")
    url = url.slice(index1+8)
    index2 = url.indexOf("&")
    url = url.slice(index2+8)
    index3 = url.indexOf("&")
    url = url.slice(index3+8)
    index4 = url.indexOf("&")
    
    num1 = index1+8
    num2 = num1+index2
    num3 = num2+8
    num4 = num3+index3
    num5 = num4+8
    num6 = num5+index4
    num7 = num6+8
    
    level1 = level.slice(num1,num2)
    level2 = level.slice(num3,num4)
    level3 = level.slice(num5,num6)
    level4 = level.slice(num7)

    levels = [level1,level2,level3,level4]

    for(i = 0;i<4;i++){
      levels[i] = decodeURIComponent(levels[i])
    }

    return levels
    
}

function createToken(){
    let chars = 'ABCDEFGHJKMNPQRSTWXYZabcdefhijkmnprstwxyz2345678';
     let maxPos = chars.length;
     var token = '';
     for (let i = 0; i < 5; i++) {
         token += chars.charAt(Math.floor(Math.random() * maxPos));
     }
     return token
}//随机生成令牌

function getJsonObj(url,callback) {
  let xmlHttpRequest = new XMLHttpRequest();
  xmlHttpRequest.open('get', url);
  xmlHttpRequest.addEventListener('load', function (e) {
    let responseText = this.responseText;
    callback(JSON.parse(responseText));
  })
  xmlHttpRequest.send(null);
}

getJsonObj(tableapi,(data) => {
  tableName = data.list[1].table_name
});




function getName(){
    baseUrl = "http://dxx.ahyouth.org.cn/api/peopleRankStage?table_name="
    url = baseUrl + tableName + "&level1=" + levels[0]+ "&level2=" + levels[1]+ "&level3=" + levels[2]+ "&level4=" + levels[3]
    getJsonObj(url,(data) => {
  names = data.list.list
  let namelist = ""
  for(i=0;i<names.length;i++){
    namelist += names[i].username + "/"
    if((i+1)%6==0)
    namelist += "\n"
    } document.getElementById('nameList').value=namelist
  alert("已爬取"+names.length+"名同学名单\n名单可编辑，请核对后再提交！")
   });
}


    
