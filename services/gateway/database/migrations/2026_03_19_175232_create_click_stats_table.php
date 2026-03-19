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
		Schema::create('click_stats', function (Blueprint $table) {
			$table->id();
			// short_code — обычный индекс для быстрой группировки статистики
			$table->string('short_code', 15)->index();
			$table->timestamp('clicked_at')->useCurrent();
			$table->string('ip', 45)->nullable(); // 45 символов для поддержки IPv6
			$table->text('user_agent')->nullable();
			$table->text('referer')->nullable();
			$table->string('country', 2)->nullable(); // ISO 3166-1 alpha-2 код
		});
	}

    /**
     * Reverse the migrations.
     */
    public function down(): void
    {
        Schema::dropIfExists('click_stats');
    }
};
