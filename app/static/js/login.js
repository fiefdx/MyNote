function loginInit (msg) {
    var r_user = "";
    var r_passwd = "";
    var r_passwd_confirm = "";

    function is_in(substr, str) {
        if(str.indexOf(substr, 0) != -1) {
            return 1;
        } else {
            return 0;
        }
    }

    !function ($) {
        $(function() {
          // carousel demo
          $('#myCarousel').carousel()
        })
    }(window.jQuery)

    $(".r_user").change(function() {
        // alert(is_in(" ", this.value));
        if(!is_in(" ", this.value) && this.value.length >= 3) {
            r_user = this.value;
            $("#r_user").attr("class","glyphicon glyphicon-ok col-xs-2");
        }
        else{
            $("#r_user").attr("class","glyphicon glyphicon-remove col-xs-2");
            alert(msg.user_name);
        }
    });

    $(".r_passwd").change(function() {
        // alert(this.value.length);
        if(!is_in(" ", this.value) && this.value.length >= 6) {
            r_passwd = this.value;
            $("#r_passwd").attr("class","glyphicon glyphicon-ok col-xs-2");
        } else {
            $("#r_passwd").attr("class","glyphicon glyphicon-remove col-xs-2");
            alert(msg.password);
        }
    });

    $(".r_passwd_confirm").keyup(function() {
        if(r_passwd.indexOf(this.value) == 0 && r_passwd.length == this.value.length) {
            r_passwd_confirm = this.value;
            $("#r_passwd_confirm").attr("class","glyphicon glyphicon-ok col-xs-2");
        } else {
            $("#r_passwd_confirm").attr("class","glyphicon glyphicon-remove col-xs-2");
        }
    });

    $("button#register").click(function() {
        // alert("check form");
        if(is_in(" ", r_user) || is_in(" ", r_passwd) || r_passwd.length < 6 || r_passwd != r_passwd_confirm) {
            alert(msg.user_name_password_error);
        } else {
            $("form#form_register").submit();
        }
    });
}