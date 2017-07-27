	$(document).ready(function($){
          var parPosition = [];
        $('.par').each(function() {
            parPosition.push($(this).offset().top);
        });

		$('a').click(function(){
			$('html, body').animate({
				scrollTop: $( $.attr(this, 'href') ).offset().top
			}, 500);
			return false;
		});

  	$('.vNav ul li a').click(function () {
			$('.vNav ul li a').removeClass('active');
				$(this).addClass('active');
		});

    $('.vNav a').hover(function() {
    	$(this).find('.label').show();
    }, function() {
    	$(this).find('.label').hide();
    });

    $(document).scroll(function(){
    	var position = $(document).scrollTop(),
          index;
      for (var i=0; i<parPosition.length; i++) {
      	if (position <= parPosition[i]) {
        	index = i;
          break;
        }
      }
		});

    $('.vNav ul li a').removeClass('active');
    	$('.vNav ul li a:eq('+index+')').addClass('active');
    });

    $('.vNav ul li a').click(function () {
			$('.vNav ul li a').removeClass('active');
			$(this).addClass('active');
		});


	});
