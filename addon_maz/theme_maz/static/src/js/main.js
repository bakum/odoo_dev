$(document).ready(function()
{
   if ($(window).width() <= 1183) {
		if ($(window).width() <= 974) {
			if ($(window).width() <= 750) {
				$('.body').removeClass('body-lg');
				$('.body').removeClass('body-md');
				$('.body').removeClass('body-sm');
				$('.body').addClass('body-xs');
				//alert('*4*');

				$('#sDropList_v').css('display','none');
				$('.indexslider').css('display','none');
				$('.cont_left').css('display','none');
				$('.header_logo').css('height','100px');
				$('.header_min').css('height','115px');
				$('.header_min table').css('height','115px');
				$('.header_cart').css('height','75px');
				$('.header_cart table').css('height','75px');

				if ($('#viewspan').html() == 'list') {
					if ($('#lang').html() == 'ru') {
						location.href = '/catalogue/' + $('#viewcat').html() + '?view=tiles';
					} else {
						location.href = '/ua/catalogue/' + $('#viewcat').html() + '?view=tiles';
					}
				}
				$('.ruk').css('display','none');

			} else {
				$('.body').removeClass('body-lg');
				$('.body').removeClass('body-md');
				$('.body').addClass('body-sm');
				$('.body').removeClass('body-xs');
				//alert('*3*');

				$('#sDropList_v').css('display','block');
				$('#sDropList').css('width','440px');
				$('.indexslider').css('display','block');
				$('.cont_left').css('display','block');
				$('.header_logo').css('height','150px');
				$('.header_min').css('height','150px');
				$('.header_min table').css('height','150px');
				$('.header_cart').css('height','150px');
				$('.header_cart table').css('height','150px');

				// if ($('#viewspan').html() == 'tiles') {
				// 	if ($('#lang').html() == 'ru') {
				// 		location.href = '/catalogue/' + $('#viewcat').html() + '?view=list';
				// 	} else {
				// 		location.href = '/ua/catalogue/' + $('#viewcat').html() + '?view=list';
				// 	}
				// }
				// $('.ruk').css('display','none');
			}
		} else {
			$('.body').removeClass('body-lg');
			$('.body').addClass('body-md');
			$('.body').removeClass('body-sm');
			$('.body').removeClass('body-xs');
			//alert('*2*');

			$('#sDropList_v').css('display','block');
			$('#sDropList').css('width','570px');
			$('.indexslider').css('display','block');
			$('.cont_left').css('display','block');
			$('.header_logo').css('height','150px');
			$('.header_min').css('height','150px');
			$('.header_min table').css('height','150px');
			$('.header_cart').css('height','150px');
			$('.header_cart table').css('height','150px');

			$('.ruk').css('display','block');
		}
	} else {
		$('.body').addClass('body-lg');
		$('.body').removeClass('body-md');
		$('.body').removeClass('body-sm');
		$('.body').removeClass('body-xs');
		//alert('*1*');

		$('#sDropList_v').css('display','block');
		$('#sDropList').css('width','570px');
		$('.indexslider').css('display','block');
		$('.cont_left').css('display','block');
		$('.header_logo').css('height','150px');
		$('.header_min').css('height','150px');
		$('.header_min table').css('height','150px');
		$('.header_cart').css('height','150px');
		$('.header_cart table').css('height','150px');

		$('.ruk').css('display','block');
	}
});