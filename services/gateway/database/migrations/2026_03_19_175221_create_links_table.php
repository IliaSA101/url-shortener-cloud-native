<?php

use Illuminate\Database\Migrations\Migration;
use Illuminate\Database\Schema\Blueprint;
use Illuminate\Support\Facades\Schema;

return new class extends Migration
{
    /**
     * Run the migrations.
     */
    public function up(): void
	{
		Schema::create('links', function (Blueprint $table) {
			$table->id();
			// short_code — наш hot path для редиректов. Уникальный индекс обязателен!
			$table->string('short_code', 15)->unique(); 
			$table->text('original_url');
			// Связь с юзерами (nullable, так как могут быть анонимные ссылки)
			$table->foreignId('user_id')->nullable()->constrained()->nullOnDelete();
			$table->timestamps();
		});
	}

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('links');
    }
};
