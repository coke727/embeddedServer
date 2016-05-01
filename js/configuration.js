$(document).ready(function($) {
    $('.accordion').find('.accordion-toggle').click(function(){

      //Expand or collapse this panel
      $(this).next().slideToggle('fast');

      //Hide the other panels
      $(".accordion-content").not($(this).next()).slideUp('fast');

    });

    $("#general").click(function(event) {
    	var frequency = document.getElementById("frequency").value;

    	if(frequency < 10) {
        	if( !confirm('A low value for frequency can spend so much power. Are you sure?') ) 
            	event.preventDefault();
        }
    });

    $("#scp").click(function(event) {
    	if( !confirm('If you are using power saving mode 3 the scp frequency could be not so acurated due to the hibernation periods.') ) {
            	event.preventDefault();
        }
    });
});

