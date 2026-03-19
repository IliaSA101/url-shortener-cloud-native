<?php

use Illuminate\Support\Facades\Route;
use App\Http\Controllers\RedirectController;

// Ловим любой короткий код после слеша
Route::get('/{code}', [RedirectController::class, 'redirect']);