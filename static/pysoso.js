$SCRIPT_ROOT = "/pysoso";


$(function()
{
	$('a#calculate').bind('click', function() {
		$.getJSON($SCRIPT_ROOT + '/_add_numbers', {
			a: $('input[name="a"]').val(),
			b: $('input[name="b"]').val()
		}, function(data) {
			$("#result").text(data.result);
		});
		return false;
	});

	$('a#edit').bind('click', function () {
		if ($(this).hasClass("active"))
		{
			$(this).removeClass("active");
			$("#bookmarks .tools").hide();
		}
		else
		{
			$(this).addClass("active");
			$("#bookmarks .tools").show();
		}
		return false;
	});

	$('.bookmarks_show').bind('click', function () {
		var ul = $(this).parents("div").children("ul");
		if (ul.is(":visible"))
		{
			ul.hide("fast");
			$(this).removeClass("active");
		}
		else
		{
			ul.show("fast");
			$(this).addClass("active");
		}

		return false;
	});

	$('#bookmarks .edit').bind('mouseover', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "underline";
	});

	$('#bookmarks .edit').bind('mouseout', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "none";
	});

	$('#bookmarks .delete').bind('mouseover', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "line-through";
	});

	$('#bookmarks .delete').bind('mouseout', function () {
		var el = $(this).parents("li").children(".bookmark")[0];
		el.style.textDecoration = "none";
	});


	$('#bookmarks .delete').bind('click', function () {
		$(this).parents("li").hide("slow");
		$.getJSON($(this).attr("href"));
		return false;
	});

	$('#bookmarks .bookmark').bind('click', function () {
		$(this).parents("li").hide("slow");
	});


});
