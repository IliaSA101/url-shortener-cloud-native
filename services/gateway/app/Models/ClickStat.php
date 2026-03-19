<?php

namespace App\Models;

use Illuminate\Database\Eloquent\Model;
use Illuminate\Database\Eloquent\Factories\HasFactory;

class ClickStat extends Model
{
    use HasFactory;

    // ОБЯЗАТЕЛЬНО: отключаем автоматические created_at и updated_at
    public $timestamps = false;

    protected $fillable = [
        'short_code',
        'clicked_at',
        'ip',
        'user_agent',
        'referer',
        'country',
    ];

    // Указываем Laravel, что поле clicked_at — это дата/время
    protected $casts = [
        'clicked_at' => 'datetime',
    ];
}