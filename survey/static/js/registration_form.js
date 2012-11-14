// 
//	jQuery Validate example script
//
//	Prepared by David Cochran
//	
//	Free for your use -- No warranties, no guarantees!
//

$(document).ready(function(){

	// Validate
	// http://bassistance.de/jquery-plugins/jquery-plugin-validation/
	// http://docs.jquery.com/Plugins/Validation/
	// http://docs.jquery.com/Plugins/Validation/validate#toptions
	
		$('#registration_form').validate({
	    rules: {
	      username: {
	        minlength: 3,
            maxlength: 30,
	        required: true,
            remote: "/account/check_username"
	      },
	      email: {
			  required: true,
			  email: true,
              minlength: 5,
              maxlength: 75,
			  remote: "/account/check_email"
			},
	      password1: {
              required: true,
              minlength: 5
          },
			password2: {
				required: true,
				equalTo: "#id_password1"
			}
	    },
		messages: {
            username: {
                remote: jQuery.format("This username is already in use")
            },
            email: {
                remote: jQuery.format("This email is already in use")
            },
		},
	    highlight: function(label) {
	    	$(label).closest('.control-group').addClass('error');
	    },
	    success: function(label) {
	    	label
	    		.text('OK!').addClass('valid')
	    		.closest('.control-group').addClass('success');
	    }
	  });
	  
}); // end document.ready