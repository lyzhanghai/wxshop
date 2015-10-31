// JavaScript Document
function increase(){
   	var num = parseInt($('#num').val());
   	if(num > 1){
   		$('#num').val(num-1);
   	}
}
function decrease(){
	var num = parseInt($('#num').val());
    $('#num').val(num+1);
}

