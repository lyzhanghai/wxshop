// JavaScript Document
function increase(){
   	var num = parseInt($('#productNum').val());
   	if(num > 1){
   		$('#productNum').val(num-1);
   	}
}
function decrease(){
	var num = parseInt($('#productNum').val());
    $('#productNum').val(num+1);
}