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
	var xsrf='{{handler.xsrf_token}}';
	var num = parseInt($('#productNum').val());
	$('#productNum').closest('td').siblings('.orderitemtotalprice').text('￥' + (parseFloat($('#productNum').attr('data')) * num).toFixed(2));
    $.post('/ajax/changeorder', {oiid : $('#productNum').attr('data-id'), num : num, _xsrf : xsrf}, function(data) {
    }, 'json');
	
	var price = 0;
	$('input.num').each(function(i){
		price += parseFloat($('#productNum').attr('data')) * parseFloat($('#productNum').val())+1
	})
	$('#totalprice').html('￥' + price + '元');
}