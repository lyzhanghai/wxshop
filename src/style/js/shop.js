// JavaScript Document
function increase(){
   	var num = parseInt($('#productNum').val());
   	if(num > 1){
   		$('#productNum').val(num-1);
   	}
   	settotalprice();
}
function decrease(){
	var num = parseInt($('#productNum').val());
    $('#productNum').val(num+1);
    settotalprice();
}

function settotalprice(){
	var price = 0;
	$('input.num').each(function(i){
		price += parseInt($(this).attr('data')) * parseInt($(this).val())
	})
	$('#totalprice').html('￥' + price + '元');
}