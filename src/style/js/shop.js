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
	$('#productNum').closest('td').siblings('.orderitemtotalprice').text('￥' + parseInt($('#productNum').attr('data')) * num);
    $.post('/ajax/changeorder', {oiid : $('#productNum').attr('data-id'), num : num, _xsrf : xsrf}, function(data) {
    }, 'json');
	
	var price = 0;
	$('input.num').each(function(i){
		price += parseInt($('#productNum').attr('data')) * parseInt($('#productNum').val())
	})
	$('#totalprice').html('￥' + price + '元');
}